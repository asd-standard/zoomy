.. PyZui benchmarks instruction file,

QZUI Benchmark Documentation
============================

Overview
--------

The QZUI Benchmark is a comprehensive performance testing tool for
PyZUI that measures rendering performance and memory consumption under
load. It continuously populates a scene with media objects while
monitoring frame timing and resource usage.

The benchmark includes **cyclical zoom and pan operations** that
simulate user interaction and stress-test the tile caching system 
by continuously changing which tiles are visible.

Table of Contents
-----------------

-  :ref:`Quick Start <quick-start>`
-  :ref:`Usage Documentation <usage-documentation>`
	-  :ref:`Basic Usage <basic-usage>`
	-  :ref:`Command Line Options <command-line-options>`
	-  :ref:`Examples <examples>`
	-  :ref:`Output Interpretation <output-interpretation>`
-  :ref:`Technical Documentation <technical-documentation>`
    -  :ref:`Architecture <architecture>`
    -  :ref:`Data Classes <data-classes>`
    -  :ref:`Benchmark Phases <benchmark-phases>`
    -  :ref:`Cyclical Movement System <cyclical-Movement-system>`
    -  :ref:`Metrics Collection <metrics-collection>`
    -  :ref:`Memory Monitoring <memory-monitoring>`
-  :ref:`Configuration Reference <configuration-reference>`
-  :ref:`Troubleshooting <troubleshooting>`

------------------------------

.. _quick-start:

Quick Start
-----------

Run a basic 30-second benchmark with zoom/pan movement:

.. code-block:: bash

   cd /path/to/pyzui
   python test/benchmarks/stress_benchmark.py

Run with custom settings:

.. code-block:: bash

   python test/benchmarks/stress_benchmark.py --duration 60 --fps 30 --objects-rate 10

Run a static benchmark (no zoom/pan):

.. code-block:: bash

   python test/benchmarks/stress_benchmark.py --no-movement

------------------------------

.. _usage-documentation:

Usage Documentation
-------------------

.. _basic-usage:

Basic Usage
~~~~~~~~~~~

The QZUI Benchmark can be run from the command line with default or
custom settings:

.. code-block:: bash

   # From the pyzui project root directory
   python test/benchmarks/stress_benchmark.py

This will:

1. Launch a PyZUI window (1280x720 by default)
2. Add 10 initial objects to the scene
3. Run for 30 seconds, adding 5 objects per second
4. Apply continuous zoom oscillation (10s cycle) and pan movement (8s cycle)
5. Display performance results when complete

.. _command-line-options:

Command-Line Options
~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 18 12 12 50

   * - Option
     - Type
     - Default
     - Description
   * - ``--duration``
     - float
     - 30.0
     - Benchmark duration in seconds
   * - ``--fps``
     - int
     - 30
     - Target framerate for dropped frame detection
   * - ``--objects-rate``
     - int
     - 5
     - Number of objects to add per second
   * - ``--initial``
     - int
     - 10
     - Initial object count before timing starts
   * - ``--width``
     - int
     - 1280
     - Viewport width in pixels
   * - ``--height``
     - int
     - 720
     - Viewport height in pixels
   * - ``--output``
     - str
     - None
     - Output file path for CSV results
   * - ``--data-dir``
     - str
     - ./data
     - Directory containing test images
   * - ``--zoom-cycle``
     - float
     - 10.0
     - Zoom oscillation period in seconds
   * - ``--pan-cycle``
     - float
     - 8.0
     - Pan oscillation period in seconds
   * - ``--zoom-amplitude``
     - float
     - 2.0
     - Zoom oscillation amplitude
   * - ``--pan-amplitude``
     - float
     - 0.3
     - Pan amplitude as fraction of viewport
   * - ``--no-movement``
     - flag
     - False
     - Disable zoom and pan (static benchmark)

.. _examples: 

Examples
~~~~~~~~

Basic benchmark with defaults (includes zoom/pan):

.. code-block:: bash

   python test/benchmarks/stress_benchmark.py

Extended benchmark with high object rate:

.. code-block:: bash

   python test/benchmarks/stress_benchmark.py --duration 120 --objects-rate 20

Export results to CSV:

.. code-block:: bash

   python test/benchmarks/stress_benchmark.py --output benchmark_results.csv

Custom viewport size:

.. code-block:: bash

   python test/benchmarks/stress_benchmark.py --width 1920 --height 1080

Use custom image directory:

.. code-block:: bash

   python test/benchmarks/stress_benchmark.py --data-dir /path/to/test/images

Fast zoom/pan cycles:

.. code-block:: bash

   python test/benchmarks/stress_benchmark.py --zoom-cycle 3 --pan-cycle 2 --zoom-amplitude 3.0

Static benchmark:

.. code-block:: bash

   python test/benchmarks/stress_benchmark.py --no-movement

Gentle movement test:

.. code-block:: bash

   python test/benchmarks/stress_benchmark.py --duration 300 --zoom-cycle 30 --pan-cycle 20 --zoom-amplitude 1.0

Full customization:

.. code-block:: bash

   python test/benchmarks/stress_benchmark.py \
       --duration 60 \
       --fps 60 \
       --objects-rate 10 \
       --initial 50 \
       --width 1920 \
       --height 1080 \
       --output results.csv \
       --data-dir ./data

.. _output-interpretation:

Output Interpretation
~~~~~~~~~~~~~~~~~~~~~

The benchmark produces output in three stages.

**1. Configuration Summary**

.. code-block:: text

   PyZUI QZUI Benchmark
   ============================================================
   Configuration:
     Target FPS:        30
     Viewport:          1280x720
     Duration:          30.0s
     Objects/second:    5
     Initial objects:   10
     Test images:       3 found
   ============================================================

**2. Progress Updates**

.. code-block:: text

   Adding 10 initial objects...
   Warming up...
   Running benchmark for 30.0s at 30 FPS target...
   Adding 5 objects/second...
     Frame 100: 15 objects, 31.2 FPS, 125.3 MB RSS
     Frame 200: 20 objects, 30.8 FPS, 132.1 MB RSS

**3. Final Results**

.. code-block:: text

   ============================================================
   BENCHMARK RESULTS
   ============================================================
   Total frames:        912
   Total time:          30.02s
   Mean FPS:            30.38
   Min FPS:             28.45
   Max FPS:             32.12
   Dropped frames:      23 (2.5%)
   Mean render time:    12.45ms
   Max render time:     45.23ms
   Peak memory (RSS):   256.7MB
   Peak memory (VMS):   512.3MB
   Final object count:  160
   ============================================================

Metric Explanations
~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 50 20

   * - Metric
     - Description
     - Healthy Range
   * - Mean FPS
     - Average frames per second
     - Close to target FPS
   * - Min FPS
     - Lowest instantaneous FPS
     - >50% of target
   * - Max FPS
     - Highest instantaneous FPS
     - Should not exceed target significantly
   * - Dropped frames
     - Frames that exceed target interval
     - <5%
   * - Mean render time
     - Average frame render time
     - <1000/target_fps ms
   * - Max render time
     - Worst-case latency
     - Watch for spikes
   * - Peak memory (RSS)
     - Max physical memory
     - Content-dependent
   * - Peak memory (VMS)
     - Max virtual memory
     - Content-dependent

------------------------------

.. _technical-documentation:

Technical Documentation
-----------------------

.. _architecture:

Architecture
~~~~~~~~~~~~

::

   StressBenchmark
   ├── BenchmarkConfig
   ├── FrameMetrics
   ├── BenchmarkResults
   └── Utility Functions

Class Hierarchy
~~~~~~~~~~~~~~~

::

   ┌─────────────────────────────────────────────────────────────┐
   │                     StressBenchmark                         │
   ├─────────────────────────────────────────────────────────────┤
   │ - __config: BenchmarkConfig                                 │
   │ - __frame_metrics: List[FrameMetrics]                       │
   │ - __temp_dir: Optional[str]                                 │
   │ - __base_zoom: float                                        │
   │ - __base_origin: Tuple[float, float]                        │
   ├─────────────────────────────────────────────────────────────┤
   │ + run() -> BenchmarkResults                                 │
   │ + print_results(results)                                    │
   │ + frame_metrics (property)                                  │
   │ - __apply_cyclical_movement(scene, elapsed)                 │
   │ - __generate_random_string_media_id()                       │
   │ - __add_random_object(scene, allow_images)                  │
   │ - __render_timed_frame(qzui, frame_num, obj_count)          │
   │ - __calculate_results()                                     │
   │ - __export_csv(filepath)                                    │
   └─────────────────────────────────────────────────────────────┘

.. _data-classes:

Data Classes
~~~~~~~~~~~~

FrameMetrics
^^^^^^^^^^^^

.. code-block:: python

   @dataclass
   class FrameMetrics:
       frame_number: int
       timestamp: float
       render_time_ms: float
       memory_rss_mb: float
       memory_vms_mb: float
       object_count: int
       dropped: bool

BenchmarkResults
^^^^^^^^^^^^^^^^

.. code-block:: python

   @dataclass
   class BenchmarkResults:
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

BenchmarkConfig
^^^^^^^^^^^^^^^

.. code-block:: python

   @dataclass
   class BenchmarkConfig:
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

.. _benchmark-phases:

Benchmark Phases
~~~~~~~~~~~~~~~~

**Phase 1: Initialization**

::

   1. Initialize TileManager
   2. Create temporary tile storage
   3. Create Qt application instance
   4. Create QZUI widget with framerate=None
   5. Create new Scene

**Phase 2: Setup**

::

   1. Add initial objects
   2. Warm-up render cycles
   3. Capture base zoom/origin
   4. Initialize timing variables

**Phase 3: Measurement Loop**

::

   while elapsed < duration:
       1. Apply movement (if enabled)
       2. Add object based on rate
       3. Render timed frame
       4. Process events
       5. Record FrameMetrics
       6. Sleep to maintain FPS
       7. Progress print every 100 frames

**Phase 4: Cleanup**

::

   1. Compute BenchmarkResults
   2. Export CSV if needed
   3. Wait for background threads
   4. Close UI and purge TileManager
   5. Remove temp dir
   6. Return results

.. _cyclical-Movement-system:

Cyclical Movement System
~~~~~~~~~~~~~~~~~~~~~~~~

Movement Equations
^^^^^^^^^^^^^^^^^^

Zoom:

::

   zoom(t) = base_zoom + amplitude * sin(2π * t / period)

Pan:

::

   pan_x(t) = amplitude * width * sin(2π * t / period_x)
   pan_y(t) = amplitude * height * sin(2π * t / period_y)

Movement Parameters
^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 20 10 50

   * - Parameter
     - Default
     - Effect
   * - zoom_cycle_sec
     - 10.0
     - Zoom oscillation period
   * - pan_cycle_sec
     - 8.0
     - Pan oscillation period
   * - zoom_amplitude
     - 2.0
     - Zoom range
   * - pan_amplitude
     - 0.3
     - Movement as fraction of viewport

.. _metrics-collection:

Metrics Collection
~~~~~~~~~~~~~~~~~~

Frame timing:

.. code-block:: python

   start = time.perf_counter()
   qzui.repaint()
   QApplication.processEvents()
   end = time.perf_counter()

Dropped frame detection:

.. code-block:: python

   dropped = render_time_ms > (1000 / target_framerate)

.. _memory-monitoring:

Memory Monitoring
~~~~~~~~~~~~~~~~~

Primary (`psutil`):

.. code-block:: python

   mem = psutil.Process(os.getpid()).memory_info()

Fallback (`/proc/self/status`):

.. code-block:: python

   with open('/proc/self/status') as f: ...

------------------------------

.. _configuration-reference:

Configuration Reference
-----------------------

Object Distribution
~~~~~~~~~~~~~~~~~~~

- 70% StringMediaObjects
- 30% TiledMediaObjects (if images available)
- 100% strings if no images found

StringMediaObject Generation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Random strings contain:

- Random hex color
- 5–50 chars
- 30% multiline probability

Position and Zoom
~~~~~~~~~~~~~~~~~

- Random X/Y within viewport
- Random zoom in [-2.0, 2.0]

Test Images
~~~~~~~~~~~

Extensions searched:

- .jpg, .jpeg
- .png
- .ppm
- .gif
- .tiff

Default directory: ``./data``

------------------------------

.. _troubleshooting:

Troubleshooting
------------------------------

Common Issues
~~~~~~~~~~~~~

No display:

- Use X11/Wayland
- Or run:

.. code-block:: bash

   xvfb-run python stress_benchmark.py

Low FPS:

- Reduce ``--objects-rate``
- Lower ``--fps``
- Use smaller viewport

Memory growth:

- Export CSV for analysis
- Inspect memory columns

Performance Tips
~~~~~~~~~~~~~~~~

1. Baseline test with zero objects
2. Increase load gradually
3. Use CSV for profiling
4. Compare multiple runs

CSV Analysis
~~~~~~~~~~~~

Example CSV structure:

.. code-block:: text

   frame_number,timestamp,render_time_ms,memory_rss_mb,...

Example Python analysis:

.. code-block:: python

   df['fps'] = 1000 / df['render_time_ms']

------------------------------

License
-------

This benchmark is part of PyZUI and licensed under GNU GPLv2.

Copyright (C) 2009  
David Roberts <d@vidr.cc>
