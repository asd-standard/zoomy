## PyZUI - Python Zooming User Interface
## Copyright (C) 2009 David Roberts <d@vidr.cc>
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
Stress Benchmark for PyZUI Performance Testing.

This module provides a comprehensive stress benchmark that launches the PyZUI
application, continuously populates the scene with images and StringMediaObjects,
and monitors frame rate performance (including dropped frames) and memory
consumption over time.

The benchmark includes cyclical zoom and pan operations to simulate realistic
user interaction and stress-test the tile caching system.

The benchmark is designed to identify performance bottlenecks and measure
how the application scales with increasing object counts and camera movement.

Usage::

    python test/benchmarks/stress_benchmark.py [options]

Options::

    --duration      : Benchmark duration in seconds (default: 30)
    --fps           : Target framerate (default: 30)
    --objects-rate  : Objects added per second (default: 5)
    --initial       : Initial object count before timing (default: 10)
    --output        : Output file for CSV results (optional)
    --zoom-cycle    : Zoom cycle period in seconds (default: 10)
    --pan-cycle     : Pan cycle period in seconds (default: 8)
    --no-movement   : Disable zoom and pan (static benchmark)

Example::

    python test/benchmarks/stress_benchmark.py --duration 60 --fps 30 --objects-rate 10
    python test/benchmarks/stress_benchmark.py --duration 30 --zoom-cycle 5 --pan-cycle 4
    python test/benchmarks/stress_benchmark.py --no-movement  # Static benchmark
"""

import os
import sys
import time
import tempfile
import shutil
import random
import string
import argparse
import csv
import math
from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Optional, Any

## Add project root to path for imports
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))

from PySide6 import QtCore, QtWidgets, QtGui

import pyzui.tilesystem.tilemanager as TileManager
import pyzui.tilesystem.tilestore as TileStore
from pyzui.objects.scene.qzui import QZUI
import pyzui.objects.scene.scene as Scene
from pyzui.objects.mediaobjects.tiledmediaobject import TiledMediaObject
from pyzui.objects.mediaobjects.stringmediaobject import StringMediaObject

## ============================================================================
## Data Classes for Metrics
## ============================================================================

@dataclass
class FrameMetrics:
    """
    Constructor :
        FrameMetrics(frame_number, timestamp, render_time_ms, memory_rss_mb,
                     memory_vms_mb, object_count, dropped)
    Parameters :
        frame_number : int
        timestamp : float
        render_time_ms : float
        memory_rss_mb : float
        memory_vms_mb : float
        object_count : int
        dropped : bool

    FrameMetrics(...) --> FrameMetrics

    Data class containing performance metrics for a single rendered frame.

    Attributes::

        frame_number   : Sequential frame identifier
        timestamp      : Unix timestamp when frame completed rendering
        render_time_ms : Time taken to render this frame in milliseconds
        memory_rss_mb  : Resident Set Size memory usage in megabytes
        memory_vms_mb  : Virtual Memory Size in megabytes
        object_count   : Number of objects in scene at time of rendering
        dropped        : True if frame exceeded target frame interval
    """
    frame_number: int
    timestamp: float
    render_time_ms: float
    memory_rss_mb: float
    memory_vms_mb: float
    object_count: int
    dropped: bool

@dataclass
class BenchmarkResults:
    """
    Constructor :
        BenchmarkResults(total_frames, total_time_sec, mean_fps, min_fps,
                         max_fps, dropped_frame_count, dropped_frame_pct,
                         mean_render_time_ms, max_render_time_ms,
                         peak_memory_rss_mb, peak_memory_vms_mb,
                         final_object_count)
    Parameters :
        total_frames : int
        total_time_sec : float
        mean_fps : float
        min_fps : float
        max_fps : float
        dropped_frame_count : int
        dropped_frame_pct : float
        mean_render_time_ms : float
        max_render_time_ms : float
        peak_memory_rss_mb : float
        peak_memory_vms_mb : float
        final_object_count : int

    BenchmarkResults(...) --> BenchmarkResults

    Data class containing aggregate benchmark results computed from all
    collected frame metrics.

    Attributes::

        total_frames        : Total number of frames rendered
        total_time_sec      : Total benchmark duration in seconds
        mean_fps            : Average frames per second over entire run
        min_fps             : Minimum instantaneous FPS (rolling window)
        max_fps             : Maximum instantaneous FPS (rolling window)
        dropped_frame_count : Number of frames that exceeded target interval
        dropped_frame_pct   : Percentage of dropped frames
        mean_render_time_ms : Average render time per frame in milliseconds
        max_render_time_ms  : Maximum render time observed in milliseconds
        peak_memory_rss_mb  : Peak RSS memory usage in megabytes
        peak_memory_vms_mb  : Peak VMS memory usage in megabytes
        final_object_count  : Number of objects at benchmark completion
    """
    total_frames: int
    total_time_sec: float
    mean_fps: float
    min_fps: float
    max_fps: float
    dropped_frame_count: int
    dropped_frame_pct: float
    mean_render_time_ms: float
    max_render_time_ms: float
    peak_memory_rss_mb: float
    peak_memory_vms_mb: float
    final_object_count: int

@dataclass
class BenchmarkConfig:
    """
    Constructor :
        BenchmarkConfig(target_framerate, viewport_size, duration_sec,
                        objects_per_second, initial_objects, test_images,
                        output_file, zoom_cycle_sec, pan_cycle_sec,
                        zoom_amplitude, pan_amplitude, enable_movement)
    Parameters :
        target_framerate : int
        viewport_size : Tuple[int, int]
        duration_sec : float
        objects_per_second : int
        initial_objects : int
        test_images : List[str]
        output_file : Optional[str]
        zoom_cycle_sec : float
        pan_cycle_sec : float
        zoom_amplitude : float
        pan_amplitude : float
        enable_movement : bool

    BenchmarkConfig(...) --> BenchmarkConfig

    Configuration data class for benchmark parameters.

    Attributes::

        target_framerate   : Target FPS for dropped frame detection
        viewport_size      : Window dimensions as (width, height)
        duration_sec       : How long to run the benchmark
        objects_per_second : Rate of adding new objects to scene
        initial_objects    : Objects to add before timing starts
        test_images        : List of image file paths to use
        output_file        : Optional path for CSV output
        zoom_cycle_sec     : Period of zoom oscillation in seconds
        pan_cycle_sec      : Period of pan oscillation in seconds
        zoom_amplitude     : Amplitude of zoom oscillation (zoom levels)
        pan_amplitude      : Amplitude of pan as fraction of viewport
        enable_movement    : Whether to enable zoom/pan movement
    """
    target_framerate: int = 30
    viewport_size: Tuple[int, int] = (1280, 720)
    duration_sec: float = 30.0
    objects_per_second: int = 5
    initial_objects: int = 10
    test_images: List[str] = field(default_factory=list)
    output_file: Optional[str] = None
    zoom_cycle_sec: float = 10.0
    pan_cycle_sec: float = 8.0
    zoom_amplitude: float = 2.0
    pan_amplitude: float = 0.3
    enable_movement: bool = True

## ============================================================================
## Memory Monitoring
## ============================================================================

def get_memory_usage() -> Tuple[float, float]:
    """
    Function :
        get_memory_usage()
    Parameters :
        None

    get_memory_usage() --> Tuple[float, float]

    Get current process memory usage in megabytes.

    Returns a tuple of (RSS, VMS) where:
    - RSS (Resident Set Size): Physical memory currently in use
    - VMS (Virtual Memory Size): Total virtual memory allocated

    Uses psutil if available, falls back to /proc/self/status on Linux,
    or returns (0.0, 0.0) if neither method is available.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem = process.memory_info()
        return mem.rss / (1024 * 1024), mem.vms / (1024 * 1024)
    except ImportError:
        pass

    ## Fallback for Linux: parse /proc/self/status
    try:
        with open('/proc/self/status', 'r') as f:
            rss = vms = 0.0
            for line in f:
                if line.startswith('VmRSS:'):
                    rss = float(line.split()[1]) / 1024  # KB to MB
                elif line.startswith('VmSize:'):
                    vms = float(line.split()[1]) / 1024  # KB to MB
            return rss, vms
    except (IOError, OSError):
        pass

    return 0.0, 0.0

## ============================================================================
## Stress Benchmark Class
## ============================================================================

class StressBenchmark:
    """
    Constructor :
        StressBenchmark(config)
    Parameters :
        config : BenchmarkConfig

    StressBenchmark(config) --> None

    Benchmark class that continuously populates a PyZUI scene while measuring
    rendering performance and memory consumption.

    The benchmark works by:
    1. Initializing the TileManager and Qt application
    2. Creating a QZUI widget with framerate limiting disabled
    3. Adding an initial set of objects to the scene
    4. Running a main loop that:
       - Adds objects at a configurable rate
       - Renders frames using direct repaint() calls
       - Measures render time, memory usage, and dropped frames
       - Collects metrics for each frame
    5. Computing aggregate statistics from all collected metrics

    Usage::

        config = BenchmarkConfig(
            target_framerate=30,
            duration_sec=60.0,
            objects_per_second=5
        )
        benchmark = StressBenchmark(config)
        results = benchmark.run()
        benchmark.print_results(results)
    """

    def __init__(self, config: BenchmarkConfig) -> None:
        """
        Constructor :
            StressBenchmark(config)
        Parameters :
            config : BenchmarkConfig

        StressBenchmark(config) --> None

        Initialize a new StressBenchmark with the given configuration.

        Sets up internal state for metric collection and stores the
        configuration parameters.
        """
        self.__config = config
        self.__frame_metrics: List[FrameMetrics] = []
        self.__temp_dir: Optional[str] = None
        self.__base_zoom: float = 0.0
        self.__base_origin: Tuple[float, float] = (0.0, 0.0)

    def __apply_cyclical_movement(self, scene: Scene.Scene,
                                   elapsed: float) -> None:
        """
        Method :
            StressBenchmark.__apply_cyclical_movement(scene, elapsed)
        Parameters :
            scene : Scene.Scene
            elapsed : float

        StressBenchmark.__apply_cyclical_movement(scene, elapsed) --> None

        Apply cyclical zoom and pan transformations to the scene.

        Uses sinusoidal oscillation for smooth, continuous movement:
        - Zoom oscillates using a sine wave based on zoom_cycle_sec
        - Pan follows a Lissajous-like pattern with different X/Y frequencies

        The movement is designed to stress-test the tile loading and caching
        system by continuously changing which tiles are visible.

        Movement is relative to the base zoom and origin captured at the
        start of the benchmark to ensure we always return to the starting view.
        """
        if not self.__config.enable_movement:
            return

        viewport_w, viewport_h = self.__config.viewport_size

        ## Calculate zoom oscillation
        ## Uses sine wave: zoom = base + amplitude * sin(2*pi*t/period)
        zoom_phase = (2.0 * math.pi * elapsed) / self.__config.zoom_cycle_sec
        target_zoom = self.__base_zoom + \
            self.__config.zoom_amplitude * math.sin(zoom_phase)

        ## Calculate pan oscillation
        ## Uses Lissajous pattern with slightly different frequencies for X/Y
        ## to create interesting movement patterns
        pan_phase_x = (2.0 * math.pi * elapsed) / self.__config.pan_cycle_sec
        pan_phase_y = (2.0 * math.pi * elapsed) / (self.__config.pan_cycle_sec * 1.3)

        pan_x = self.__config.pan_amplitude * viewport_w * math.sin(pan_phase_x)
        pan_y = self.__config.pan_amplitude * viewport_h * math.sin(pan_phase_y)

        target_origin_x = self.__base_origin[0] + pan_x
        target_origin_y = self.__base_origin[1] + pan_y

        ## Apply zoom change relative to current
        ## scene.zoom() expects a delta, not absolute value
        current_zoom = scene.zoomlevel
        zoom_delta = target_zoom - current_zoom
        if abs(zoom_delta) > 0.001:
            scene.zoom(zoom_delta)

        ## Apply pan by setting origin directly
        ## Origin is stored in scene._x and scene._y via the origin property
        scene._x = target_origin_x
        scene._y = target_origin_y

    def __generate_random_string_media_id(self) -> str:
        """
        Method :
            StressBenchmark.__generate_random_string_media_id()
        Parameters :
            None

        StressBenchmark.__generate_random_string_media_id() --> str

        Generate a random media_id string for StringMediaObject creation.

        The format follows the StringMediaObject specification:
        'string:rrggbb:text' where rrggbb is a hex color code and text
        is the content to display.

        Occasionally includes newline characters to create multi-line
        strings for more diverse testing.
        """
        ## Generate random hex color
        color = ''.join(random.choices('0123456789ABCDEF', k=6))

        ## Generate random text content
        text_len = random.randint(5, 50)
        text = ''.join(random.choices(string.ascii_letters + ' ', k=text_len))

        ## Occasionally add newlines for multi-line strings (30% chance)
        if random.random() > 0.7:
            mid = len(text) // 2
            text = text[:mid] + '\\n' + text[mid:]

        return f"string:{color}:{text}"

    def __screen_to_scene_coords(self, screen_x: float, screen_y: float,
                                   scene: Scene.Scene) -> Tuple[float, float]:
        """
        Method :
            StressBenchmark.__screen_to_scene_coords(screen_x, screen_y, scene)
        Parameters :
            screen_x : float
            screen_y : float
            scene : Scene.Scene

        StressBenchmark.__screen_to_scene_coords(screen_x, screen_y, scene)
            --> Tuple[float, float]

        Convert screen coordinates to scene coordinates.

        The conversion formula is derived from MediaObject.topleft:
            screen_x = scene.origin[0] + scene_x * (2 ** scene.zoomlevel)

        Solving for scene coordinates:
            scene_x = (screen_x - scene.origin[0]) * (2 ** -scene.zoomlevel)
        """
        scene_x = (screen_x - scene.origin[0]) * (2 ** -scene.zoomlevel)
        scene_y = (screen_y - scene.origin[1]) * (2 ** -scene.zoomlevel)
        return (scene_x, scene_y)

    def __add_random_object(self, scene: Scene.Scene,
                            allow_images: bool = True) -> None:
        """
        Method :
            StressBenchmark.__add_random_object(scene, allow_images)
        Parameters :
            scene : Scene.Scene
            allow_images : bool

        StressBenchmark.__add_random_object(scene, allow_images) --> None

        Add a randomly positioned media object to the scene.

        Object type distribution (when allow_images=True):
        - 70% StringMediaObjects (always available)
        - 30% TiledMediaObjects (if test images are configured)

        When allow_images=False, only StringMediaObjects are added.
        This is useful near the end of benchmarks to avoid starting
        converter threads that won't complete before cleanup.

        Objects are positioned randomly within the viewport bounds
        with random zoom levels between -2 and 2.

        Screen coordinates are converted to scene coordinates using
        the scene's current origin and zoom level to ensure objects
        appear distributed across the visible viewport area.
        """
        viewport_w, viewport_h = self.__config.viewport_size

        ## Determine object type: 70% strings, 30% images (if available and allowed)
        use_image = (allow_images and self.__config.test_images and
                     random.random() > 0.7)

        if use_image:
            media_id = random.choice(self.__config.test_images)
            obj = TiledMediaObject(media_id, scene, autofit=True)
        else:
            media_id = self.__generate_random_string_media_id()
            obj = StringMediaObject(media_id, scene)

        ## Generate random screen position within viewport
        screen_x = random.uniform(0, viewport_w)
        screen_y = random.uniform(0, viewport_h)

        ## Convert screen coordinates to scene coordinates
        ## This ensures objects appear distributed across the visible area
        scene_x, scene_y = self.__screen_to_scene_coords(screen_x, screen_y, scene)
        obj.pos = (scene_x, scene_y)

        ## Random zoom level for variety
        obj.zoomlevel = random.uniform(-2, 2)

        scene.add(obj)

    def __render_timed_frame(self, qzui: QZUI, frame_num: int,
                             object_count: int) -> FrameMetrics:
        """
        Method :
            StressBenchmark.__render_timed_frame(qzui, frame_num, object_count)
        Parameters :
            qzui : QZUI
            frame_num : int
            object_count : int

        StressBenchmark.__render_timed_frame(qzui, frame_num, object_count)
            --> FrameMetrics

        Render a single frame and measure its performance metrics.

        Performs the following:
        1. Captures memory usage before rendering
        2. Calls qzui.repaint() to force immediate rendering
        3. Processes Qt events to complete the paint cycle
        4. Measures elapsed time
        5. Determines if frame was "dropped" (exceeded target interval)

        The dropped flag is set when the render time exceeds the target
        frame interval (1/target_framerate seconds).
        """
        target_interval_ms = 1000.0 / self.__config.target_framerate

        ## Capture memory before render
        rss_mb, vms_mb = get_memory_usage()

        ## Time the render operation
        start = time.perf_counter()
        qzui.repaint()
        QtWidgets.QApplication.processEvents()
        end = time.perf_counter()

        render_time_ms = (end - start) * 1000
        dropped = render_time_ms > target_interval_ms

        return FrameMetrics(
            frame_number=frame_num,
            timestamp=end,
            render_time_ms=render_time_ms,
            memory_rss_mb=rss_mb,
            memory_vms_mb=vms_mb,
            object_count=object_count,
            dropped=dropped
        )

    def __calculate_results(self) -> BenchmarkResults:
        """
        Method :
            StressBenchmark.__calculate_results()
        Parameters :
            None

        StressBenchmark.__calculate_results() --> BenchmarkResults

        Calculate aggregate results from collected frame metrics.

        Computes:
        - Mean FPS over the entire benchmark run
        - Min/Max instantaneous FPS using a rolling window of 10 frames
        - Dropped frame count and percentage
        - Mean and max render times
        - Peak memory usage

        Raises ValueError if no metrics were collected.
        """
        if not self.__frame_metrics:
            raise ValueError("No frame metrics collected")

        total_frames = len(self.__frame_metrics)
        first_ts = self.__frame_metrics[0].timestamp
        last_ts = self.__frame_metrics[-1].timestamp
        total_time = last_ts - first_ts

        render_times = [m.render_time_ms for m in self.__frame_metrics]
        dropped = [m for m in self.__frame_metrics if m.dropped]

        ## Calculate instantaneous FPS using rolling window
        fps_values = []
        window_size = 10
        for i in range(window_size, total_frames):
            dt = (self.__frame_metrics[i].timestamp -
                  self.__frame_metrics[i - window_size].timestamp)
            if dt > 0:
                fps_values.append(window_size / dt)

        return BenchmarkResults(
            total_frames=total_frames,
            total_time_sec=total_time,
            mean_fps=total_frames / total_time if total_time > 0 else 0,
            min_fps=min(fps_values) if fps_values else 0,
            max_fps=max(fps_values) if fps_values else 0,
            dropped_frame_count=len(dropped),
            dropped_frame_pct=100.0 * len(dropped) / total_frames,
            mean_render_time_ms=sum(render_times) / len(render_times),
            max_render_time_ms=max(render_times),
            peak_memory_rss_mb=max(m.memory_rss_mb for m in self.__frame_metrics),
            peak_memory_vms_mb=max(m.memory_vms_mb for m in self.__frame_metrics),
            final_object_count=self.__frame_metrics[-1].object_count
        )

    def __export_csv(self, filepath: str) -> None:
        """
        Method :
            StressBenchmark.__export_csv(filepath)
        Parameters :
            filepath : str

        StressBenchmark.__export_csv(filepath) --> None

        Export collected frame metrics to a CSV file.

        Creates a CSV file with columns for all FrameMetrics fields,
        allowing for detailed analysis and visualization of the
        benchmark results.
        """
        if not self.__frame_metrics:
            return

        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'frame_number', 'timestamp', 'render_time_ms',
                'memory_rss_mb', 'memory_vms_mb', 'object_count', 'dropped'
            ])
            writer.writeheader()
            for metrics in self.__frame_metrics:
                writer.writerow(asdict(metrics))

    def run(self) -> BenchmarkResults:
        """
        Method :
            StressBenchmark.run()
        Parameters :
            None

        StressBenchmark.run() --> BenchmarkResults

        Execute the stress benchmark and return aggregate results.

        The benchmark executes the following phases:

        1. **Initialization Phase**:
           - Initialize TileManager with default settings
           - Create temporary directory for tile storage and temp files
           - Redirect tempfile.tempdir to capture all temporary files
           - Create Qt application instance
           - Create QZUI widget with framerate limiting disabled

        2. **Setup Phase**:
           - Create a new scene
           - Add initial objects to establish baseline
           - Perform warm-up renders to initialize caches

        3. **Measurement Phase**:
           - Run main loop for configured duration
           - Add objects at configured rate
           - Render frames and collect metrics
           - Print progress updates every 100 frames

        4. **Cleanup Phase**:
           - Close QZUI widget and purge TileManager
           - Restore original tempfile.tempdir setting
           - Remove temporary directory (includes tiles and temp PPM files)
           - Export CSV if output file configured

        Returns BenchmarkResults containing aggregate statistics.
        """
        ## Save original tempdir to restore later
        original_tempdir = tempfile.tempdir

        ## Initialize TileManager
        TileManager.init()
        self.__temp_dir = tempfile.mkdtemp()
        TileStore.tile_dir = self.__temp_dir

        ## Redirect all temporary files to our temp directory
        ## This ensures TiledMediaObject's temporary PPM files are also cleaned up
        tempfile.tempdir = self.__temp_dir

        ## Create or get Qt application
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication([])

        ## Create QZUI widget
        qzui = QZUI()
        qzui.framerate = None  # Disable internal timer for manual control
        qzui.resize(*self.__config.viewport_size)
        qzui.show()

        ## Create scene
        scene = Scene.new()
        qzui.scene = scene

        try:
            ## Add initial objects
            print(f"Adding {self.__config.initial_objects} initial objects...")
            for _ in range(self.__config.initial_objects):
                self.__add_random_object(scene)

            ## Warm-up phase: render several frames to initialize caches
            print("Warming up...")
            for _ in range(10):
                qzui.repaint()
                QtWidgets.QApplication.processEvents()

            ## Capture base zoom and origin for cyclical movement
            self.__base_zoom = scene.zoomlevel
            self.__base_origin = (scene._x, scene._y)

            ## Main benchmark loop
            print(f"Running benchmark for {self.__config.duration_sec}s "
                  f"at {self.__config.target_framerate} FPS target...")
            print(f"Adding {self.__config.objects_per_second} objects/second...")
            if self.__config.enable_movement:
                print(f"Zoom cycle: {self.__config.zoom_cycle_sec}s, "
                      f"Pan cycle: {self.__config.pan_cycle_sec}s")
            else:
                print("Movement disabled (static benchmark)")

            start_time = time.perf_counter()
            frame_num = 0
            last_add_time = start_time
            object_count = self.__config.initial_objects
            add_interval = 1.0 / self.__config.objects_per_second
            target_frame_interval = 1.0 / self.__config.target_framerate

            ## Stop adding images 3 seconds before end to allow converters to finish
            image_cutoff_time = self.__config.duration_sec - 3.0

            while (time.perf_counter() - start_time) < self.__config.duration_sec:
                current_time = time.perf_counter()
                elapsed = current_time - start_time

                ## Apply cyclical zoom and pan movement
                self.__apply_cyclical_movement(scene, elapsed)

                ## Add objects at configured rate
                ## Stop adding images near the end to let converters complete
                if (current_time - last_add_time) >= add_interval:
                    allow_images = (elapsed < image_cutoff_time)
                    self.__add_random_object(scene, allow_images=allow_images)
                    object_count += 1
                    last_add_time = current_time

                ## Render frame and collect metrics
                metrics = self.__render_timed_frame(qzui, frame_num, object_count)
                self.__frame_metrics.append(metrics)
                frame_num += 1

                ## Progress output every 100 frames
                if frame_num % 100 == 0:
                    current_fps = frame_num / elapsed if elapsed > 0 else 0
                    zoom_info = f"zoom={scene.zoomlevel:.2f}" \
                        if self.__config.enable_movement else ""
                    print(f"  Frame {frame_num}: {object_count} objects, "
                          f"{current_fps:.1f} FPS, "
                          f"{metrics.memory_rss_mb:.1f} MB RSS {zoom_info}")

                ## Try to maintain target framerate
                frame_end = time.perf_counter()
                sleep_time = target_frame_interval - (frame_end - current_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            ## Calculate and return results
            results = self.__calculate_results()

            ## Export CSV if configured
            if self.__config.output_file:
                self.__export_csv(self.__config.output_file)
                print(f"Exported metrics to {self.__config.output_file}")

            return results

        finally:
            ## Restore original tempdir setting first, so any late converter
            ## errors don't try to write to our temp directory
            tempfile.tempdir = original_tempdir

            ## Allow pending converter threads to complete or fail gracefully
            ## TiledMediaObjects start async converter threads that may still
            ## be running when we reach cleanup
            print("Waiting for background tasks to complete...")
            for _ in range(10):
                QtWidgets.QApplication.processEvents()
                time.sleep(0.1)

            ## Cleanup: close widget and purge tile manager
            qzui.close()
            TileManager.purge()

            ## Process any remaining Qt events
            QtWidgets.QApplication.processEvents()

            ## Cleanup temporary directory (contains tiles and temp PPM files)
            if self.__temp_dir:
                shutil.rmtree(self.__temp_dir, ignore_errors=True)

    def print_results(self, results: BenchmarkResults) -> None:
        """
        Method :
            StressBenchmark.print_results(results)
        Parameters :
            results : BenchmarkResults

        StressBenchmark.print_results(results) --> None

        Print formatted benchmark results to stdout.

        Displays all aggregate metrics in a readable table format
        with appropriate units and precision.
        """
        print("\n" + "=" * 60)
        print("BENCHMARK RESULTS")
        print("=" * 60)
        print(f"Total frames:        {results.total_frames}")
        print(f"Total time:          {results.total_time_sec:.2f}s")
        print(f"Mean FPS:            {results.mean_fps:.2f}")
        print(f"Min FPS:             {results.min_fps:.2f}")
        print(f"Max FPS:             {results.max_fps:.2f}")
        print(f"Dropped frames:      {results.dropped_frame_count} "
              f"({results.dropped_frame_pct:.1f}%)")
        print(f"Mean render time:    {results.mean_render_time_ms:.2f}ms")
        print(f"Max render time:     {results.max_render_time_ms:.2f}ms")
        print(f"Peak memory (RSS):   {results.peak_memory_rss_mb:.1f}MB")
        print(f"Peak memory (VMS):   {results.peak_memory_vms_mb:.1f}MB")
        print(f"Final object count:  {results.final_object_count}")
        print("=" * 60)

    @property
    def frame_metrics(self) -> List[FrameMetrics]:
        """
        Property :
            StressBenchmark.frame_metrics
        Parameters :
            None

        StressBenchmark.frame_metrics --> List[FrameMetrics]

        Return the list of collected frame metrics.

        This property provides access to the raw per-frame data for
        custom analysis or visualization.
        """
        return self.__frame_metrics.copy()

## ============================================================================
## Utility Functions
## ============================================================================

def find_test_images(data_dir: str) -> List[str]:
    """
    Function :
        find_test_images(data_dir)
    Parameters :
        data_dir : str
            - Path to directory containing test images

    find_test_images(data_dir) --> List[str]

    Scan a directory for image files suitable for benchmark testing.

    Searches for files with extensions: .jpg, .jpeg, .png, .ppm, .gif, .tiff

    Returns a list of absolute paths to found image files.
    Returns an empty list if the directory doesn't exist.
    """
    supported_extensions = ('.jpg', '.jpeg', '.png', '.ppm', '.gif', '.tiff')
    images = []

    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            if filename.lower().endswith(supported_extensions):
                images.append(os.path.join(data_dir, filename))

    return images

def parse_arguments() -> BenchmarkConfig:
    """
    Function :
        parse_arguments()
    Parameters :
        None

    parse_arguments() --> BenchmarkConfig

    Parse command-line arguments and return a BenchmarkConfig.

    Supports the following arguments:
    - --duration: Benchmark duration in seconds (default: 30)
    - --fps: Target framerate (default: 30)
    - --objects-rate: Objects added per second (default: 5)
    - --initial: Initial object count (default: 10)
    - --width: Viewport width (default: 1280)
    - --height: Viewport height (default: 720)
    - --output: Output file path for CSV results
    - --data-dir: Directory containing test images
    - --zoom-cycle: Zoom oscillation period in seconds (default: 10)
    - --pan-cycle: Pan oscillation period in seconds (default: 8)
    - --zoom-amplitude: Zoom oscillation amplitude (default: 2.0)
    - --pan-amplitude: Pan amplitude as viewport fraction (default: 0.3)
    - --no-movement: Disable zoom and pan (static benchmark)
    """
    parser = argparse.ArgumentParser(
        description='PyZUI Stress Benchmark - Performance testing tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python stress_benchmark.py --duration 60 --fps 30
  python stress_benchmark.py --objects-rate 10 --output results.csv
  python stress_benchmark.py --data-dir /path/to/images --duration 120
  python stress_benchmark.py --zoom-cycle 5 --pan-cycle 4
  python stress_benchmark.py --no-movement  # Static benchmark (no zoom/pan)
        """
    )

    parser.add_argument(
        '--duration', type=float, default=30.0,
        help='Benchmark duration in seconds (default: 30)'
    )
    parser.add_argument(
        '--fps', type=int, default=30,
        help='Target framerate for dropped frame detection (default: 30)'
    )
    parser.add_argument(
        '--objects-rate', type=int, default=5,
        help='Number of objects to add per second (default: 5)'
    )
    parser.add_argument(
        '--initial', type=int, default=10,
        help='Initial object count before timing starts (default: 10)'
    )
    parser.add_argument(
        '--width', type=int, default=1280,
        help='Viewport width in pixels (default: 1280)'
    )
    parser.add_argument(
        '--height', type=int, default=720,
        help='Viewport height in pixels (default: 720)'
    )
    parser.add_argument(
        '--output', type=str, default=None,
        help='Output file path for CSV results (optional)'
    )
    parser.add_argument(
        '--data-dir', type=str, default=None,
        help='Directory containing test images (default: ../../data)'
    )
    parser.add_argument(
        '--zoom-cycle', type=float, default=10.0,
        help='Zoom oscillation period in seconds (default: 10)'
    )
    parser.add_argument(
        '--pan-cycle', type=float, default=8.0,
        help='Pan oscillation period in seconds (default: 8)'
    )
    parser.add_argument(
        '--zoom-amplitude', type=float, default=2.0,
        help='Zoom oscillation amplitude in zoom levels (default: 2.0)'
    )
    parser.add_argument(
        '--pan-amplitude', type=float, default=0.3,
        help='Pan amplitude as fraction of viewport (default: 0.3)'
    )
    parser.add_argument(
        '--no-movement', action='store_true',
        help='Disable zoom and pan movement (static benchmark)'
    )

    args = parser.parse_args()

    ## Find test images
    if args.data_dir:
        data_dir = args.data_dir
    else:
        data_dir = os.path.join(os.path.dirname(__file__), '../../data')

    test_images = find_test_images(data_dir)

    return BenchmarkConfig(
        target_framerate=args.fps,
        viewport_size=(args.width, args.height),
        duration_sec=args.duration,
        objects_per_second=args.objects_rate,
        initial_objects=args.initial,
        test_images=test_images,
        output_file=args.output,
        zoom_cycle_sec=args.zoom_cycle,
        pan_cycle_sec=args.pan_cycle,
        zoom_amplitude=args.zoom_amplitude,
        pan_amplitude=args.pan_amplitude,
        enable_movement=not args.no_movement
    )

## ============================================================================
## Main Entry Point
## ============================================================================

def main() -> None:
    """
    Function :
        main()
    Parameters :
        None

    main() --> None

    Main entry point for the stress benchmark.

    Parses command-line arguments, creates a StressBenchmark instance,
    executes the benchmark, and prints results.
    """
    config = parse_arguments()

    print("PyZUI Stress Benchmark")
    print("=" * 60)
    print(f"Configuration:")
    print(f"  Target FPS:        {config.target_framerate}")
    print(f"  Viewport:          {config.viewport_size[0]}x{config.viewport_size[1]}")
    print(f"  Duration:          {config.duration_sec}s")
    print(f"  Objects/second:    {config.objects_per_second}")
    print(f"  Initial objects:   {config.initial_objects}")
    print(f"  Test images:       {len(config.test_images)} found")
    if config.enable_movement:
        print(f"  Movement:          Enabled")
        print(f"  Zoom cycle:        {config.zoom_cycle_sec}s "
              f"(amplitude: {config.zoom_amplitude})")
        print(f"  Pan cycle:         {config.pan_cycle_sec}s "
              f"(amplitude: {config.pan_amplitude * 100:.0f}% viewport)")
    else:
        print(f"  Movement:          Disabled (static)")
    if config.output_file:
        print(f"  Output file:       {config.output_file}")
    print("=" * 60)

    benchmark = StressBenchmark(config)
    results = benchmark.run()
    benchmark.print_results(results)

if __name__ == '__main__':
    main()
