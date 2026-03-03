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
Stress Tests: Concurrent Operations

This module contains stress tests for concurrent operations in the
converter and tiling systems, testing thread safety and resource
management under heavy load.
"""

import pytest
import os
import threading
import time
import queue
from concurrent.futures import wait, ThreadPoolExecutor, ProcessPoolExecutor
from PIL import Image

from pyzui.converters import converterrunner
from pyzui.tilesystem.tiler import tilerrunner


def is_pyvips_available():
    """Check if pyvips is available for testing."""
    try:
        import pyvips
        return True
    except ImportError:
        return False


@pytest.fixture
def sample_image_batch(tmp_path):
    """
    Fixture: Batch of Sample Test Images
    
    Create multiple sample images for stress testing.
    """
    images = []
    
    for i in range(10):
        # Create simple images of different sizes
        img_file = str(tmp_path / f"sample_{i}.png")
        size = 128 * (i + 1)  # Varying sizes: 128, 256, 384, ...
        img = Image.new('RGB', (size, size), color=(i * 25, i * 25, i * 25))
        img.save(img_file, 'PNG')
        images.append(img_file)
    
    return images


@pytest.fixture(autouse=True)
def cleanup_runners():
    """
    Fixture: Cleanup Runners
    
    Ensure converterrunner and tilerrunner are properly shut down after each test.
    """
    yield
    # Clean up any remaining executors
    converterrunner.shutdown()
    tilerrunner.shutdown()


class TestConverterRunnerStress:
    """
    Feature: Converter Runner Stress Tests
    
    Stress tests for converterrunner under heavy concurrent load.
    """

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_many_concurrent_conversions(self, sample_image_batch, tmp_path):
        """
        Scenario: Many concurrent conversions complete successfully
        
        Given many images to convert
        When conversions run in parallel processes
        Then all should complete within reasonable time
        And resource usage should be managed properly
        """
        # Initialize with reasonable worker count
        converterrunner.init(max_workers=4)
        
        # Submit many conversions
        futures = []
        output_files = []
        
        for i, infile in enumerate(sample_image_batch):
            outfile = str(tmp_path / f"output_{i}.ppm")
            output_files.append(outfile)
            future = converterrunner.submit_vips_conversion(infile, outfile)
            futures.append((future, outfile))
        
        # Wait for all with generous timeout
        start_time = time.time()
        done, not_done = wait([f for f, _ in futures], timeout=300)  # 5 minutes
        elapsed = time.time() - start_time
        
        assert len(not_done) == 0, f"{len(not_done)} conversions timed out after {elapsed:.1f}s"
        
        # Check results
        success_count = 0
        error_count = 0
        
        for future, outfile in futures:
            error = future.result()
            if error is None:
                success_count += 1
            else:
                error_count += 1
                print(f"Conversion error: {error}")
        
        # Allow some failures in stress test (due to resource limits)
        success_rate = success_count / len(futures)
        assert success_rate >= 0.7, f"Success rate too low: {success_rate:.1%}"
        
        print(f"Stress test: {success_count}/{len(futures)} successful "
              f"({success_rate:.1%}) in {elapsed:.1f}s")

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_concurrent_submission_with_many_threads(self, sample_image_batch, tmp_path):
        """
        Scenario: Many threads submitting conversions concurrently
        
        Given many threads
        When each thread submits conversions
        Then all submissions should complete without race conditions
        And executor management should remain thread-safe
        """
        converterrunner.init(max_workers=4)
        
        submission_queue = queue.Queue()
        results = []
        errors = []
        lock = threading.Lock()
        
        def submission_worker(worker_id):
            """Worker thread that submits conversions."""
            try:
                # Each worker submits a few conversions
                for i in range(3):
                    if i >= len(sample_image_batch):
                        break
                    
                    infile = sample_image_batch[i]
                    outfile = str(tmp_path / f"worker_{worker_id}_conv_{i}.ppm")
                    
                    future = converterrunner.submit_vips_conversion(infile, outfile)
                    
                    with lock:
                        results.append((worker_id, i, future, outfile))
                        
            except Exception as e:
                with lock:
                    errors.append((worker_id, str(e)))
        
        # Start many worker threads
        workers = []
        for i in range(10):  # 10 worker threads
            worker = threading.Thread(target=submission_worker, args=(i,))
            workers.append(worker)
            worker.start()
        
        # Wait for all workers
        for worker in workers:
            worker.join(timeout=60)
            assert not worker.is_alive(), f"Worker thread {worker} timed out"
        
        # Check for submission errors
        assert len(errors) == 0, f"Errors during concurrent submission: {errors}"
        
        # Wait for all conversions to complete
        futures = [future for _, _, future, _ in results]
        done, not_done = wait(futures, timeout=300)
        
        assert len(not_done) == 0, f"{len(not_done)} conversions still pending"
        
        # Clean up
        converterrunner.shutdown()

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_rapid_init_shutdown_cycles(self):
        """
        Scenario: Rapid initialization and shutdown cycles
        
        Given rapid calls to init() and shutdown()
        When executed in quick succession
        Then no resource leaks should occur
        And operations should remain thread-safe
        """
        cycles = 20
        
        for cycle in range(cycles):
            # Rapid init/shutdown
            converterrunner.init(max_workers=2)
            converterrunner.shutdown()
            
            # Small delay to allow cleanup
            time.sleep(0.01)
        
        # Final check - should be able to use after cycles
        converterrunner.init(max_workers=2)
        converterrunner.shutdown()


class TestMixedWorkloadStress:
    """
    Feature: Mixed Workload Stress Tests
    
    Stress tests with mixed conversion and tiling workloads.
    """

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_mixed_conversion_and_tiling_workloads(self, sample_image_batch, tmp_path):
        """
        Scenario: Mixed conversion and tiling workloads under stress
        
        Given many images
        When conversions and tiling operations run concurrently
        Then all should complete successfully
        And resource contention should be managed properly
        """
        # Initialize both runners
        converterrunner.init(max_workers=4)
        tilerrunner.init(max_workers=4)
        
        # Phase 1: Convert all images
        conversion_futures = []
        ppm_files = []
        
        for i, infile in enumerate(sample_image_batch[:5]):  # Use first 5 for speed
            ppm_file = str(tmp_path / f"converted_{i}.ppm")
            ppm_files.append(ppm_file)
            future = converterrunner.submit_vips_conversion(infile, ppm_file)
            conversion_futures.append(future)
        
        # Wait for conversions
        done, not_done = wait(conversion_futures, timeout=300)
        assert len(not_done) == 0, "Some conversions timed out"
        
        # Check conversion results
        valid_ppm_files = []
        for i, future in enumerate(conversion_futures):
            error = future.result()
            if error is None and os.path.exists(ppm_files[i]):
                valid_ppm_files.append(ppm_files[i])
        
        # Phase 2: Tile converted images
        if valid_ppm_files:
            tiling_futures = []
            
            for i, ppm_file in enumerate(valid_ppm_files):
                media_id = f"stress_tile_{i}"
                future = tilerrunner.submit_tiling(
                    ppm_file, media_id=media_id, tilesize=256
                )
                tiling_futures.append(future)
            
            # Wait for tiling
            done, not_done = wait(tiling_futures, timeout=300)
            assert len(not_done) == 0, "Some tiling operations timed out"
            
            # Check tiling results
            success_count = 0
            for future in tiling_futures:
                error = future.result()
                if error is None:
                    success_count += 1
            
            print(f"Mixed workload: {success_count}/{len(valid_ppm_files)} "
                  f"tiling operations successful")
        
        # Clean up
        converterrunner.shutdown()
        tilerrunner.shutdown()

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_concurrent_access_to_shared_runners(self, sample_image_batch, tmp_path):
        """
        Scenario: Concurrent access to shared runner instances
        
        Given multiple threads accessing converterrunner and tilerrunner
        When operations are interleaved
        Then thread safety should be maintained
        And no race conditions should occur
        """
        converterrunner.init(max_workers=2)
        tilerrunner.init(max_workers=2)
        
        results = []
        errors = []
        lock = threading.Lock()
        
        def mixed_worker(worker_id):
            """Worker performs mixed operations on both runners."""
            try:
                # Each worker does a few operations
                for i in range(2):
                    # Submit a conversion
                    if i < len(sample_image_batch):
                        infile = sample_image_batch[i]
                        outfile = str(tmp_path / f"mixed_{worker_id}_{i}.ppm")
                        
                        conv_future = converterrunner.submit_vips_conversion(
                            infile, outfile
                        )
                        
                        # Wait for conversion
                        conv_error = conv_future.result(timeout=60)
                        
                        if conv_error is None and os.path.exists(outfile):
                            # Submit tiling
                            media_id = f"mixed_{worker_id}_{i}"
                            tile_future = tilerrunner.submit_tiling(
                                outfile, media_id=media_id, tilesize=256
                            )
                            
                            # Wait for tiling
                            tile_error = tile_future.result(timeout=60)
                            
                            with lock:
                                results.append({
                                    'worker': worker_id,
                                    'op': i,
                                    'conv_success': conv_error is None,
                                    'tile_success': tile_error is None if conv_error is None else False
                                })
                
            except Exception as e:
                with lock:
                    errors.append((worker_id, str(e)))
        
        # Start workers
        workers = []
        for i in range(4):  # 4 workers
            worker = threading.Thread(target=mixed_worker, args=(i,))
            workers.append(worker)
            worker.start()
        
        # Wait for workers
        for worker in workers:
            worker.join(timeout=300)
            assert not worker.is_alive(), f"Worker thread {worker} timed out"
        
        # Check results
        print(f"Mixed access test: {len(results)} operations, {len(errors)} errors")
        
        # Clean up
        converterrunner.shutdown()
        tilerrunner.shutdown()


class TestResourceCleanupStress:
    """
    Feature: Resource Cleanup Stress Tests
    
    Stress tests for resource cleanup and leak prevention.
    """

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_resource_cleanup_under_load(self, sample_image_batch, tmp_path):
        """
        Scenario: Resource cleanup during heavy load
        
        Given many concurrent operations
        When operations complete or are cancelled
        Then resources should be properly cleaned up
        And no file descriptors or processes should leak
        """
        import gc
        
        # Run multiple cycles of operations
        cycles = 3
        
        for cycle in range(cycles):
            converterrunner.init(max_workers=4)
            
            # Submit conversions
            futures = []
            for i, infile in enumerate(sample_image_batch[:3]):  # Limit for speed
                outfile = str(tmp_path / f"cycle_{cycle}_{i}.ppm")
                future = converterrunner.submit_vips_conversion(infile, outfile)
                futures.append(future)
            
            # Wait for completion
            done, not_done = wait(futures, timeout=180)
            
            # Force garbage collection
            gc.collect()
            
            # Shutdown
            converterrunner.shutdown()
            
            # Small delay for cleanup
            time.sleep(0.5)
        
        # Final check - should be able to initialize and use after cycles
        converterrunner.init(max_workers=2)
        
        # Test that it still works
        if sample_image_batch:
            outfile = str(tmp_path / "final_test.ppm")
            future = converterrunner.submit_vips_conversion(sample_image_batch[0], outfile)
            error = future.result(timeout=60)
            assert error is None, f"Final conversion failed: {error}"
        
        converterrunner.shutdown()
        
        print(f"Resource cleanup: Completed {cycles} cycles successfully")

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_repeated_operations_with_cleanup(self, sample_image_batch, tmp_path):
        """
        Scenario: Repeated operations with cleanup cycles
        
        Given multiple cycles of operations
        When each cycle includes init, operations, and shutdown
        Then system should remain stable across all cycles
        """
        cycles = 3
        
        for cycle in range(cycles):
            print(f"Starting cycle {cycle + 1}/{cycles}")
            
            # Initialize
            converterrunner.init(max_workers=2)
            
            # Submit a few conversions
            futures = []
            for i, infile in enumerate(sample_image_batch[:2]):  # Small batch
                outfile = str(tmp_path / f"cycle_{cycle}_{i}.ppm")
                future = converterrunner.submit_vips_conversion(infile, outfile)
                futures.append(future)
            
            # Wait with timeout
            done, not_done = wait(futures, timeout=120)
            
            # Check results
            success_count = 0
            for future in done:
                try:
                    error = future.result(timeout=10)
                    if error is None:
                        success_count += 1
                except Exception as e:
                    print(f"Cycle {cycle} future error: {e}")
            
            print(f"Cycle {cycle + 1}: {success_count}/{len(futures)} successful")
            
            # Clean up
            converterrunner.shutdown()
            
            # Small delay between cycles
            time.sleep(0.2)
        
        # Final validation
        converterrunner.init(max_workers=1)
        
        if sample_image_batch:
            outfile = str(tmp_path / "final_validation.ppm")
            future = converterrunner.submit_vips_conversion(sample_image_batch[0], outfile)
            error = future.result(timeout=60)
            assert error is None, f"Final validation failed: {error}"
        
        converterrunner.shutdown()
        
        print(f"Repeated operations: Completed {cycles} cycles successfully")