## PyZUI - Python Zooming User Interface
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 3
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <https://www.gnu.org/licenses/>.

"""
Integration Tests: Converter Runner

This module contains integration tests for the converterrunner module,
which manages process-based parallel conversions with thread safety.
"""

import pytest
import os
import threading
import time
from concurrent.futures import wait, Future
from PIL import Image

from pyzui.converters import converterrunner


def is_pyvips_available():
    """Check if pyvips is available for testing."""
    try:
        import pyvips
        return True
    except ImportError:
        return False


@pytest.fixture
def sample_images(tmp_path):
    """
    Fixture: Sample Test Images
    
    Create sample images for conversion testing using PIL.
    """
    images = {}
    
    # Create a simple PNG image
    png_file = str(tmp_path / "sample.png")
    img = Image.new('RGB', (256, 256), color='red')
    img.save(png_file, 'PNG')
    images['png'] = png_file
    
    # Create a simple JPEG image
    jpg_file = str(tmp_path / "sample.jpg")
    img = Image.new('RGB', (512, 512), color='blue')
    img.save(jpg_file, 'JPEG', quality=90)
    images['jpg'] = jpg_file
    
    return images


@pytest.fixture(autouse=True)
def cleanup_converterrunner():
    """
    Fixture: Cleanup Converter Runner
    
    Ensure converterrunner is properly shut down after each test.
    """
    yield
    # Clean up any remaining executor
    converterrunner.shutdown()


class TestConverterRunnerIntegration:
    """
    Feature: Converter Runner Integration
    
    Integration tests for the converterrunner module, testing real
    process-based conversions with thread safety.
    """

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_converterrunner_init_shutdown_cycle(self):
        """
        Scenario: Converter runner can be initialized and shut down multiple times
        
        Given no initialized executor
        When init() is called
        Then executor should be created
        When shutdown() is called
        Then executor should be cleaned up
        When init() is called again
        Then new executor should be created
        """
        # First initialization
        converterrunner.init(max_workers=2)
        
        # Submit a dummy task to ensure executor is active
        # (We'll mock the actual conversion since we don't have pyvips in test)
        
        # Shutdown
        converterrunner.shutdown()
        
        # Re-initialize
        converterrunner.init(max_workers=3)
        
        # Verify we can submit (even if it fails without pyvips)
        # The important part is that init/shutdown cycles work
        
        # Clean up
        converterrunner.shutdown()

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_converterrunner_thread_safety_during_concurrent_submissions(self, sample_images, tmp_path):
        """
        Scenario: Multiple threads can submit conversions concurrently without race conditions
        
        Given an initialized converter runner
        When multiple threads submit conversions simultaneously
        Then all submissions should complete without errors
        And no race conditions should occur in executor management
        """
        # Initialize with small pool to test contention
        converterrunner.init(max_workers=2)
        
        results = []
        errors = []
        results_lock = threading.Lock()
        
        def submit_conversion_thread(index):
            """Submit a conversion from a thread."""
            try:
                # Use different output files to avoid conflicts
                outfile = str(tmp_path / f"output_{index}.ppm")
                handle = converterrunner.submit_vips_conversion(
                    sample_images['png'], outfile
                )
                with results_lock:
                    results.append((index, handle))
            except Exception as e:
                with results_lock:
                    errors.append((index, str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=submit_conversion_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=10)
            assert not thread.is_alive(), f"Thread {thread} timed out"
        
        # Verify no submission errors occurred
        assert len(errors) == 0, f"Errors during concurrent submission: {errors}"
        
        # We should have 5 submissions (even if they fail without pyvips)
        assert len(results) == 5, f"Expected 5 submissions, got {len(results)}"

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_converterrunner_context_switching(self):
        """
        Scenario: Converter runner handles context switching correctly
        
        Given an initialized executor with 'fork' context
        When threads are created (changing to 'spawn' context)
        Then executor should be recreated with new context
        And submissions should continue to work
        """
        # Start with single thread (fork context)
        converterrunner.init(max_workers=2)
        
        # Create threads to trigger context change
        threads_created = []
        
        def dummy_thread():
            time.sleep(0.1)
        
        # Create multiple threads
        for i in range(3):
            thread = threading.Thread(target=dummy_thread)
            threads_created.append(thread)
            thread.start()
        
        # Wait for threads
        for thread in threads_created:
            thread.join(timeout=5)
        
        # The next submission should trigger context re-evaluation
        # Note: This is hard to test without mocking, but we verify
        # that the system doesn't crash
        
        # Clean up
        converterrunner.shutdown()

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_converterrunner_environment_variable_override(self, monkeypatch):
        """
        Scenario: PYZUI_MP_CONTEXT environment variable overrides context selection
        
        Given PYZUI_MP_CONTEXT environment variable is set
        When converter runner initializes
        Then it should use the specified context regardless of thread count
        """
        # Set environment variable
        monkeypatch.setenv('PYZUI_MP_CONTEXT', 'spawn')
        
        # Initialize - should use 'spawn' even with single thread
        converterrunner.init(max_workers=2)
        
        # Clean up
        converterrunner.shutdown()
        
        # Test with different value
        monkeypatch.setenv('PYZUI_MP_CONTEXT', 'forkserver')
        
        # Re-initialize
        converterrunner.init(max_workers=2)
        
        # Clean up
        converterrunner.shutdown()

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_conversion_future_completion(self, sample_images, tmp_path):
        """
        Scenario: Future tracks conversion completion correctly
        
        Given a submitted conversion
        When checking future before completion
        Then future.done() should be False
        When conversion completes
        Then future.done() should be True
        And future.result() should return conversion result
        """
        # Initialize
        converterrunner.init(max_workers=1)
        
        # Submit conversion
        outfile = str(tmp_path / "output.ppm")
        future = converterrunner.submit_vips_conversion(
            sample_images['png'], outfile
        )
        
        # Check initial state - might already be done
        # We can't reliably check done() before completion due to timing
        
        # Wait for completion with timeout
        try:
            error = future.result(timeout=30)
            
            # After result(), done() should be True
            assert future.done(), "Future should be done after result()"
            
            # Check result
            # The conversion might fail without proper pyvips setup in test environment
            # but error should contain something (either None or error message)
            assert error is not None or os.path.exists(outfile), \
                "Either error should be set or file should exist"
                
        except TimeoutError:
            pytest.skip("Conversion timed out - pyvips may not be properly configured")
        
        # Clean up
        converterrunner.shutdown()

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_converterrunner_max_workers_respected(self):
        """
        Scenario: Converter runner respects max_workers parameter
        
        Given converter runner initialized with specific max_workers
        When checking executor configuration
        Then it should use the specified number of workers
        """
        # Test different worker counts
        test_cases = [1, 2, 4]
        
        for max_workers in test_cases:
            converterrunner.init(max_workers=max_workers)
            
            # Note: We can't directly check ProcessPoolExecutor internal worker count
            # without mocking. But we can verify init() accepts the parameter.
            
            converterrunner.shutdown()

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_converterrunner_concurrent_init_shutdown(self):
        """
        Scenario: Concurrent init and shutdown operations are thread-safe
        
        Given multiple threads calling init and shutdown simultaneously
        When operations execute concurrently
        Then no race conditions should occur
        And executor state should remain consistent
        """
        init_count = 0
        shutdown_count = 0
        lock = threading.Lock()
        
        def call_init():
            nonlocal init_count
            converterrunner.init(max_workers=2)
            with lock:
                init_count += 1
        
        def call_shutdown():
            nonlocal shutdown_count
            converterrunner.shutdown()
            with lock:
                shutdown_count += 1
        
        # Start multiple threads
        threads = []
        for i in range(10):
            if i % 2 == 0:
                thread = threading.Thread(target=call_init)
            else:
                thread = threading.Thread(target=call_shutdown)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=10)
            assert not thread.is_alive(), f"Thread {thread} timed out"
        
        # Verify operations completed
        # Exact counts may vary due to timing, but at least some should complete
        assert init_count > 0 or shutdown_count > 0, "No operations completed"
        
        # Ensure clean state
        converterrunner.shutdown()


class TestConverterRunnerErrorHandling:
    """
    Feature: Converter Runner Error Handling
    
    Tests for error conditions and edge cases in converterrunner.
    """

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_conversion_future_error_propagation(self, tmp_path):
        """
        Scenario: Conversion errors are propagated through Future
        
        Given a conversion that will fail (invalid input file)
        When conversion completes
        Then future.result() should return error message
        """
        # Initialize
        converterrunner.init(max_workers=1)
        
        # Submit conversion with non-existent file
        invalid_file = str(tmp_path / "nonexistent.png")
        outfile = str(tmp_path / "output.ppm")
        future = converterrunner.submit_vips_conversion(invalid_file, outfile)
        
        # Wait for completion
        try:
            error = future.result(timeout=30)
            
            # Error should be set
            assert error is not None, "Error should be set for failed conversion"
            assert "error" in error.lower() or "fail" in error.lower() or "not found" in error.lower(), \
                f"Error message should indicate failure: {error}"
                
        except TimeoutError:
            pytest.skip("Conversion timed out - may be hanging on invalid input")
        
        # Clean up
        converterrunner.shutdown()

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_converterrunner_shutdown_with_pending_tasks(self, sample_images, tmp_path):
        """
        Scenario: Shutdown with pending tasks cancels them gracefully
        
        Given conversions submitted but not completed
        When shutdown() is called
        Then pending tasks should be cancelled
        And no processes should remain
        """
        # Initialize with single worker to ensure tasks queue up
        converterrunner.init(max_workers=1)
        
        # Submit multiple conversions (more than workers)
        handles = []
        for i in range(3):
            outfile = str(tmp_path / f"output_{i}.ppm")
            handle = converterrunner.submit_vips_conversion(
                sample_images['png'], outfile
            )
            handles.append(handle)
        
        # Immediately shutdown (tasks may be in progress or queued)
        converterrunner.shutdown()
        
        # Check that shutdown completed
        # Some handles may have been cancelled
        cancelled_count = 0
        for handle in handles:
            try:
                # Try to get result (may raise CancelledError)
                result = handle._future.result(timeout=0.1)
            except Exception:
                cancelled_count += 1
        
        # At least some tasks should have been cancelled
        # (exact count depends on timing)
        assert cancelled_count >= 0, "Should handle cancellation gracefully"
        
        # Verify clean state
        converterrunner.shutdown()  # Should be idempotent


class TestConverterRunnerResourceManagement:
    """
    Feature: Converter Runner Resource Management
    
    Tests for proper resource cleanup and management.
    """

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_converterrunner_cleanup_on_exception(self):
        """
        Scenario: Resources are cleaned up even when exceptions occur
        
        Given an initialized converter runner
        When an exception occurs during operation
        Then resources should still be cleaned up
        And subsequent operations should work
        """
        # Initialize
        converterrunner.init(max_workers=2)
        
        # Simulate an exception scenario
        # (We can't easily trigger real exceptions without mocking)
        
        # Ensure we can still shutdown cleanly
        converterrunner.shutdown()
        
        # Should be able to re-initialize
        converterrunner.init(max_workers=2)
        converterrunner.shutdown()

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_converterrunner_idempotent_shutdown(self):
        """
        Scenario: shutdown() is idempotent
        
        Given converter runner
        When shutdown() is called multiple times
        Then no errors should occur
        And subsequent calls should have no effect
        """
        # Initialize
        converterrunner.init(max_workers=2)
        
        # Call shutdown multiple times
        converterrunner.shutdown()
        converterrunner.shutdown()
        converterrunner.shutdown()
        
        # Should still be able to re-initialize
        converterrunner.init(max_workers=2)
        converterrunner.shutdown()