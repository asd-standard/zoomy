Tiled media object
==================

Tiled media objects are the objects that need to be tiled in order to be 
efficently zoomed in the Zui. These objects media gets first converted into
ppm file format and then given to the Tiler/PPMTiler system, the first class
handles the tile pyramid as folder structure and tile sizes. Tile sizes are
then passed to PPMTiler wich handle the actual tile image creation form the 
initial ppm file.

Here we have the whole application flow::     

	┌─────────────────────────────────────────────────────────────────┐
	│ 1. USER ACTION: Add media to scene                              │
	│    scene.add(TiledMediaObject("image.jpg", scene))              │
	└────────────────────┬────────────────────────────────────────────┘
	                     │
	┌────────────────────▼────────────────────────────────────────────┐
	│ 2. TiledMediaObject.__init__(media_id, scene, autofit=True)     │
	│                                                                 │
	│    • Check if already tiled: TileManager.tiled(media_id)        │
	│    • If NOT tiled, determine file type and converter:           │
	│                                                                 │
	│      ┌──────────────────────────────────────────────┐           │
	│      │ File Type Detection:                         │           │
	│      │  • .pdf     → PDFConverter                   │           │
	│      │  • .ppm     → No conversion (direct use)     │           │
	│      │  • others   → VipsConverter                  │           │
	│      │    (.jpg, .png, .gif, .tiff, etc.)           │           │
	│      └──────────────────────────────────────────────┘           │
	└────────────────────┬────────────────────────────────────────────┘
	                     │
	┌────────────────────▼────────────────────────────────────────────┐
	│ 3. CONVERTER PHASE (if needed)                                  │
	│    converter = PDFConverter/VipsConverter(infile, tmpfile.ppm)  │
	│    converter.start()  # Runs in separate thread                 │
	│                                                                 │
	│    • Converts source file to PPM format                         │
	│    • Saves to temporary file: /tmp/tmpXXXXXX.ppm                │
	│    • Sets converter.progress (0.0 → 1.0)                        │
	└────────────────────┬────────────────────────────────────────────┘
	                     │
	┌────────────────────▼────────────────────────────────────────────┐
	│ 4. RENDER LOOP (TiledMediaObject.render() called by scene)      │
	│                                                                 │
	│    • If converter.progress == 1.0 and tiler is None:            │
	│      → Start tiling process                                     │
	└────────────────────┬────────────────────────────────────────────┘
	                     │
	┌────────────────────▼────────────────────────────────────────────┐
	│ 5. TILER INITIALIZATION                                         │
	│    __run_tiler():                                               │
	│      • Determine tile format (jpg if source is jpg, else png)   │
	│      • Create PPMTiler(ppmfile, media_id, filext)               │
	│      • tiler.start()  # Runs in separate thread                 │
	└────────────────────┬────────────────────────────────────────────┘
	                     │
	┌────────────────────▼────────────────────────────────────────────┐
	│ 6. PPMTiler.__init__(infile, media_id, filext, tilesize=256)    │
	│    Inherits from Tiler                                          │
	│                                                                 │
	│    • Opens PPM file                                             │
	│    • Reads PPM header: read_ppm_header(f)                       │
	│    • Gets image dimensions (width, height)                      │
	│    • Sets __outpath = TileStore.get_media_path(media_id)        │
	│      → ~/.pyzui/tilestore/<media_id_hash>/                      │
	└────────────────────┬────────────────────────────────────────────┘
	                     │
	┌────────────────────▼────────────────────────────────────────────┐
	│ 7. Tiler.run() - THE TILING PROCESS                             │
	│                                                                 │
	│    Step 7a: Calculate tile pyramid                              │
	│    ┌──────────────────────────────────────────────────┐         │
	│    │ • maxtilelevel = calculate_maxtilelevel()        │         │
	│    │   (How many zoom levels needed)                  │         │
	│    │ • numtiles = calculate_numtiles()                │         │
	│    │   (Total tiles across all levels)                │         │
	│    │ • Calculate grid: numtiles_across × numtiles_down│         │
	│    └──────────────────────────────────────────────────┘         │
	│                                                                 │
	│    Step 7b: Lock disk access                                    │
	│    ┌─────────────────────────────────────────────────┐          │
	│    │ with TileStore.disk_lock:                       │          │
	│    │   __tiles(tilelevel=0, row=0)  # Recursive!     │          │
	│    └─────────────────────────────────────────────────┘          │
	└────────────────────┬────────────────────────────────────────────┘
	                     │ 
	┌────────────────────▼────────────────────────────────────────────┐
	│ 8. __tiles() - RECURSIVE TILE GENERATION                        │
	│    (Called for each zoom level, starting from highest detail)   │
	│                                                                 │
	│    For tilelevel=0 (original resolution):                       │
	│    ┌─────────────────────────────────────────────────┐          │
	│    │ a) __load_row_from_file(row)                    │          │
	│    │    • Read scanlines from PPM using _scanchunk() │          │ 
	│    │    • Create Tile objects from raw pixel data    │          │
	│    │    • Build complete row of tiles                │          │
	│    │                                                 │          │
	│    │ b) __savetile(tile, tilelevel, row, col)        │          │
	│    │    • tile_id = (media_id, level, row, col)      │          │
	│    │    • filename = TileStore.get_tile_path(...)    │          │
	│    │    • tile.save(filename) → Saves to disk!       │          │
	│    └─────────────────────────────────────────────────┘          │
	│                                                                 │
	│    For tilelevel > 0 (lower resolutions):                       │
	│    ┌─────────────────────────────────────────────────┐          │
	│    │ a) Get previous level tiles via recursion       │          │
	│    │ b) __mergerows(row_a, row_b)                    │          │
	│    │    • Combine 4 tiles (2×2) into 1 tile          │          │
	│    │    • Tile.merged(t1, t2, t3, t4)                │          │
	│    │ c) __savetile(...) each merged tile             │          │
	│    └─────────────────────────────────────────────────┘          │
	└────────────────────┬────────────────────────────────────────────┘
	                     │
	┌────────────────────▼────────────────────────────────────────────┐
	│ 9. TILE STORAGE: TileStore.get_tile_path()                      │ 
	│                                                                 │
	│    Directory structure created:                                 │
	│    ~/.pyzui/tilestore/                                          │
	│    └── <media_id_hash>/                                         │
	│        ├── metadata.json  (width, height, tilesize, etc.)       │
	│        ├── 0/             (Level 0: full resolution)            │
	│        │   ├── 0/                                               │
	│        │   │   ├── 0.jpg   (tile at row=0, col=0)               │
	│        │   │   ├── 1.jpg   (tile at row=0, col=1)               │
	│        │   │   └── ...                                          │
	│        │   ├── 1/                                               │
	│        │   │   ├── 0.jpg   (tile at row=1, col=0)               │
	│        │   │   └── ...                                          │
	│        ├── 1/             (Level 1: 50% scale)                  │
	│        │   └── 0/0.jpg                                          │
	│        ├── 2/             (Level 2: 25% scale)                  │
	│        └── ...            (More levels as needed)               │
	│                                                                 │
	│    File naming: <tilelevel>/<row>/<col>.<filext>                │
	└────────────────────┬────────────────────────────────────────────┘
	                     │
	┌────────────────────▼────────────────────────────────────────────┐
	│ 10. METADATA STORAGE                                            │
	│     TileStore.write_metadata(media_id, ...)                     │
	│                                                                 │
	│     Saves to: ~/.pyzui/tilestore/<hash>/metadata.json           │
	│     Content:                                                    │
	│     {                                                           │
	│       "filext": "jpg",                                          │
	│       "tilesize": 256,                                          │
	│       "width": 4096,                                            │
	│       "height": 3072,                                           │
	│       "maxtilelevel": 4,                                        │
	│       "aspect_ratio": 1.333,                                    │
	│       "tiled": true                                             │
	│     }                                                           │
	└────────────────────┬────────────────────────────────────────────┘
	                     │
	┌────────────────────▼────────────────────────────────────────────┐
	│ 11. RENDERING: TiledMediaObject.render()                        │
	│                                                                 │
	│     • TileManager.get_tile(tile_id) loads tiles from disk       │
	│     • Tiles are cached in TileCache (LRU cache)                 │
	│     • __render_tileblock() combines visible tiles               │
	│     • Scales tileblock to screen resolution                     │
	│     • Draws to painter (displayed on screen)                    │
	└─────────────────────────────────────────────────────────────────┘
