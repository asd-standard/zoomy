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

"""Tiled media object editing dialog with image manipulation options."""

from typing import Optional, Tuple, Literal
import os
import tempfile


from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QDialogButtonBox,
    QWidget, QLabel, QHBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QTransform, QImage

from pyzui.tilesystem import tilemanager as TileManager
from pyzui.logger import get_logger
from pyzui.objects.mediaobjects.tiledmediaobject import TiledMediaObject
from pyzui.converters.vipsconverter import VipsConverter


class ModifyTiledMediaObjectDialog:
    """
    Constructor :
        ModifyTiledMediaObjectDialog(mediaobject)
    Parameters :
        mediaobject : TiledMediaObject

    ModifyTiledMediaObjectDialog(mediaobject) --> None

    Display the tiled media object with image manipulation options.
    Shows the top tile of the tiled media object and provides buttons
    for image manipulation (rotate, invert colors, black and white).
    """
    def __init__(self, mediaobject) -> None:
        """
        Method :
            ModifyTiledMediaObjectDialog.__init__(mediaobject)
        Parameters :
            mediaobject : TiledMediaObject

        ModifyTiledMediaObjectDialog.__init__(mediaobject) --> None

        Initialize the dialog with the given mediaobject.
        Loads the top tile (0,0,0) of the tiled media object.
        """
        self.mediaobject = mediaobject
        self.media_id = mediaobject._media_id if mediaobject else None
        self.tile_image = None
        self.current_rotation: Literal[0, 90, 180, 270] = 0  # Track rotation angle in degrees
        self.invert_colors: bool = False  # Track invert colors state
        self.black_and_white: bool = False  # Track black and white state

        # Initialize logger
        self.__logger = get_logger('ModifyTiledMediaObjectDialog')

        # Try to load the top tile
        if self.media_id:
            
            try:
                tile = TileManager.get_tile((self.media_id, 0, 0, 0))
                # Access the private __image attribute (Tile private attribute)
                # This is a PIL.ImageQt.ImageQt object
                if hasattr(tile, '_Tile__image'):
                    self.tile_image = tile._Tile__image
                    self.__logger.debug(f"Successfully loaded tile for media_id: {self.media_id}")
            except Exception as e:
                self.__logger.error(f"Error loading tile: {e}")
                self.tile_image = None

    def _create_button_panel(self) -> QWidget:
        """
        Method :
            ModifyTiledMediaObjectDialog._create_button_panel()
        Parameters :
            None

        ModifyTiledMediaObjectDialog._create_button_panel() --> QWidget

        Creates the button panel with image manipulation options.
        """
        button_panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Create buttons for image manipulation
        rotate_left_btn = QPushButton("Rotate Left")
        rotate_left_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        rotate_left_btn.clicked.connect(self._on_rotate_left)

        rotate_right_btn = QPushButton("Rotate Right")
        rotate_right_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        rotate_right_btn.clicked.connect(self._on_rotate_right)

        invert_colors_btn = QPushButton("Invert Colors")
        invert_colors_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        invert_colors_btn.clicked.connect(self._on_invert_colors)

        black_white_btn = QPushButton("Black and White")
        black_white_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        black_white_btn.clicked.connect(self._on_black_white)

        # Add buttons to layout
        layout.addWidget(rotate_left_btn)
        layout.addWidget(rotate_right_btn)
        layout.addWidget(invert_colors_btn)
        layout.addWidget(black_white_btn)
        layout.addStretch()

        button_panel.setLayout(layout)
        return button_panel

    def _create_image_panel(self) -> QWidget:
        """
        Method :
            ModifyTiledMediaObjectDialog._create_image_panel()
        Parameters :
            None

        ModifyTiledMediaObjectDialog._create_image_panel() --> QWidget

        Creates the image display panel showing the top tile.
        """
        image_panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        # Create label to display the tile image
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        if self.tile_image:
            # Convert QImage to QPixmap and display
            pixmap = QPixmap.fromImage(self.tile_image)
            # Scale the image to fit nicely in the dialog
            scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("No image available")
            self.image_label.setStyleSheet("QLabel { background-color: #ddd; padding: 20px; }")
            self.image_label.setMinimumSize(200, 100)

        layout.addWidget(self.image_label, alignment=Qt.AlignTop | Qt.AlignHCenter)
        layout.addStretch()
        image_panel.setLayout(layout)
        return image_panel

    def _main_dialog(self) -> QDialog:
        """
        Method :
            ModifyTiledMediaObjectDialog._main_dialog()
        Parameters :
            None

        ModifyTiledMediaObjectDialog._main_dialog() --> QDialog

        Creates and configures the main dialog window.
        """
        dialog = QDialog()
        dialog.setWindowTitle("Tiled Media Object Options")
        dialog.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        # Create main layout
        main_layout = QHBoxLayout(dialog)

        # Create image panel (left side)
        image_panel = self._create_image_panel()

        # Create button panel (right side)
        button_panel = self._create_button_panel()
        button_panel.setFixedWidth(200)

        # Add panels to main layout
        main_layout.addWidget(image_panel, stretch=1)
        main_layout.addWidget(button_panel, stretch=0)

        # Create Apply/Cancel buttons at the bottom
        button_layout = QVBoxLayout()
        button_layout.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Cancel, dialog)
        buttons.button(QDialogButtonBox.Apply).clicked.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        # Create a container for the main content and buttons
        container = QWidget()
        container_layout = QVBoxLayout(container)

        content_widget = QWidget()
        content_widget.setLayout(main_layout)

        container_layout.addWidget(content_widget)
        container_layout.addWidget(buttons)

        # Set the container as the dialog's main widget
        final_layout = QVBoxLayout(dialog)
        final_layout.addWidget(container)

        # Adjust dialog size to fit content
        dialog.adjustSize()

        return dialog

    def _run_dialog(self) -> Tuple[bool, Optional[str]]:
        """
        Method :
            ModifyTiledMediaObjectDialog._run_dialog()
        Parameters :
            None

        ModifyTiledMediaObjectDialog._run_dialog() --> Tuple[bool, Optional[str]]

        Runs the dialog and returns the result.
        Returns (ok, media_id) where ok is True if accepted.
        If rotation occurred, replaces the mediaobject in the scene.
        """
        dialog = self._main_dialog()

        # Run dialog and get result
        if dialog.exec() == QDialog.Accepted:
            # Check if any transformation was applied
            has_transformations = (
                self.current_rotation != 0 or
                self.invert_colors or
                self.black_and_white
            )

            if has_transformations:
                self.__logger.info(f"OK pressed - applying transformations: "
                                   f"rotation={self.current_rotation}°, "
                                   f"invert={self.invert_colors}, "
                                   f"b&w={self.black_and_white}")

                # Get the original source file
                infile = self.mediaobject._TiledMediaObject__tmpfile
                if not infile or not os.path.exists(infile):
                    self.__logger.error(f"Source file not found: {infile}")
                    return False, None

                # Create unique temp file for transformed output
                fd, outfile = tempfile.mkstemp('.ppm')
                os.close(fd)

                # Use VipsConverter with all transformation parameters
                self.__logger.info(f"Converting with VipsConverter: {infile} -> {outfile}")
                converter = VipsConverter(
                    infile, outfile,
                    rotation=self.current_rotation,
                    invert_colors=self.invert_colors,
                    black_and_white=self.black_and_white
                )
                converter.run()

                if converter.error:
                    self.__logger.error(f"VipsConverter failed: {converter.error}")
                    return False, None

                # Replace the mediaobject with the transformed version
                self._replace_mediaobject_with_rotated(outfile)
                return True, outfile
            else:
                return True, self.media_id
        else:
            return False, None

    def _update_image_display(self) -> None:
        """
        Method :
            ModifyTiledMediaObjectDialog._update_image_display()
        Parameters :
            None

        ModifyTiledMediaObjectDialog._update_image_display() --> None

        Update the image display with current rotation, invert, and grayscale effects.
        """
        if self.tile_image:
            # Start with a copy of the original image
            image = QImage(self.tile_image)

            # Apply black and white (grayscale) if enabled
            if self.black_and_white:
                image = image.convertToFormat(QImage.Format_Grayscale8)
                # Convert back to RGB for further processing
                image = image.convertToFormat(QImage.Format_RGB32)

            # Apply color inversion if enabled
            if self.invert_colors:
                image.invertPixels()

            # Convert QImage to QPixmap
            pixmap = QPixmap.fromImage(image)

            # Apply rotation transformation
            if self.current_rotation != 0:
                transform = QTransform()
                transform.rotate(self.current_rotation)
                pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)

            # Scale the image to fit nicely in the dialog
            scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)


    def _replace_mediaobject_with_rotated(self, rotated_ppm_path: str) -> bool:
        """
        Method :
            ModifyTiledMediaObjectDialog._replace_mediaobject_with_rotated(rotated_ppm_path)
        Parameters :
            rotated_ppm_path : str

        ModifyTiledMediaObjectDialog._replace_mediaobject_with_rotated(rotated_ppm_path) --> bool

        Remove the current mediaobject from scene and add the rotated PPM as a new mediaobject.
        Returns True if successful, False otherwise.
        """
        try:
            # Get the scene
            scene = self.mediaobject._scene

            # Store the old mediaobject's position and zoom for the new one
            old_topleft = self.mediaobject.topleft
            old_bottomright = self.mediaobject.bottomright
            old_centre = self.mediaobject.centre
            old_zoomlevel = self.mediaobject.zoomlevel

            # Clear selection references before removing to prevent stale rectangle drawing
            if scene.selection == self.mediaobject:
                scene.selection = None
            if scene.right_selection == self.mediaobject:
                scene.right_selection = None

            # Remove the old mediaobject from the scene
            self.__logger.info("Removing old mediaobject from scene")
            scene.remove(self.mediaobject)

            # Create a new TiledMediaObject with the rotated PPM
            self.__logger.info(f"Creating new TiledMediaObject with rotated PPM: {rotated_ppm_path}")
            new_mediaobject = TiledMediaObject(rotated_ppm_path, scene, autofit=False)
            new_mediaobject._TiledMediaObject__tmpfile = rotated_ppm_path

            # Set the new mediaobject to the same position and zoom as the old one
            new_mediaobject.fit((old_topleft[0], old_topleft[1], old_bottomright[0], old_bottomright[1]))
            new_mediaobject.centre = old_centre
            new_mediaobject.zoomlevel = old_zoomlevel

            # Add the new mediaobject to the scene
            self.__logger.info("Adding new mediaobject to scene")
            scene.add(new_mediaobject)



            self.__logger.info("Successfully replaced mediaobject with rotated version")
            return True

        except Exception as e:
            self.__logger.error(f"Error replacing mediaobject: {e}")
            return False

    # Button handlers
    def _on_rotate_left(self) -> None:
        """
        Method :
            ModifyTiledMediaObjectDialog._on_rotate_left()
        Parameters :
            None

        ModifyTiledMediaObjectDialog._on_rotate_left() --> None

        Rotate the image 90 degrees counter-clockwise (left).
        Updates preview only; actual rotation applied on OK.
        """
        self.current_rotation = (self.current_rotation - 90) % 360
        self._update_image_display()
        self.__logger.debug(f"Rotated left - current rotation: {self.current_rotation}°")

    def _on_rotate_right(self) -> None:
        """
        Method :
            ModifyTiledMediaObjectDialog._on_rotate_right()
        Parameters :
            None

        ModifyTiledMediaObjectDialog._on_rotate_right() --> None

        Rotate the image 90 degrees clockwise (right).
        Updates preview only; actual rotation applied on OK.
        """
        self.current_rotation = (self.current_rotation + 90) % 360
        self._update_image_display()
        self.__logger.debug(f"Rotated right - current rotation: {self.current_rotation}°")

    def _on_invert_colors(self) -> None:
        """
        Method :
            ModifyTiledMediaObjectDialog._on_invert_colors()
        Parameters :
            None

        ModifyTiledMediaObjectDialog._on_invert_colors() --> None

        Toggle invert colors effect.
        Updates preview only; actual effect applied on OK.
        """
        self.invert_colors = not self.invert_colors
        self._update_image_display()
        self.__logger.debug(f"Invert colors toggled: {self.invert_colors}")

    def _on_black_white(self) -> None:
        """
        Method :
            ModifyTiledMediaObjectDialog._on_black_white()
        Parameters :
            None

        ModifyTiledMediaObjectDialog._on_black_white() --> None

        Toggle black and white (grayscale) effect.
        Updates preview only; actual effect applied on OK.
        """
        self.black_and_white = not self.black_and_white
        self._update_image_display()
        self.__logger.debug(f"Black and white toggled: {self.black_and_white}")
