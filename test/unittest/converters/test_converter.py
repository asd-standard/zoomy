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

import pytest
from threading import Thread
from pyzui.converters.converter import Converter

class TestConverter:
    """
    Feature: Base Converter Class

    This test suite validates the Converter base class which provides common functionality
    for converting various file formats, with threading support and progress tracking.
    """

    def test_init(self):
        """
        Scenario: Initialize a converter

        Given input and output file paths
        When a Converter is instantiated
        Then it should store the file paths correctly
        And initialize progress to 0.0
        And error should be None
        And it should be a Thread instance
        """
        converter = Converter("input.jpg", "output.png")
        assert converter._infile == "input.jpg"
        assert converter._outfile == "output.png"
        assert converter._progress == 0.0
        assert converter.error is None
        assert isinstance(converter, Thread)

    def test_progress_property_initial(self):
        """
        Scenario: Check initial progress

        Given a newly created Converter
        When reading the progress property
        Then it should return 0.0
        """
        converter = Converter("input.jpg", "output.png")
        assert converter.progress == 0.0

    def test_progress_property_after_update(self):
        """
        Scenario: Read updated progress

        Given a Converter with updated internal progress
        When reading the progress property
        Then it should return the updated value
        """
        converter = Converter("input.jpg", "output.png")
        converter._progress = 0.5
        assert converter.progress == 0.5

    def test_progress_property_completed(self):
        """
        Scenario: Check completion progress

        Given a Converter with progress set to 1.0
        When reading the progress property
        Then it should return 1.0
        """
        converter = Converter("input.jpg", "output.png")
        converter._progress = 1.0
        assert converter.progress == 1.0

    def test_str_representation(self):
        """
        Scenario: Get string representation

        Given a Converter instance
        When str() is called
        Then it should return the expected format with file paths
        """
        converter = Converter("input.jpg", "output.png")
        assert str(converter) == "Converter(input.jpg, output.png)"

    def test_repr_representation(self):
        """
        Scenario: Get repr representation

        Given a Converter instance
        When repr() is called
        Then it should return the expected format with quoted file paths
        """
        converter = Converter("input.jpg", "output.png")
        assert repr(converter) == "Converter('input.jpg', 'output.png')"

    def test_run_method_exists(self):
        """
        Scenario: Call abstract run method

        Given a Converter instance
        When the run method is called
        Then it should return None as it is abstract
        """
        converter = Converter("input.jpg", "output.png")
        result = converter.run()
        assert result is None

    def test_error_attribute_default(self):
        """
        Scenario: Check default error state

        Given a newly created Converter
        When checking the error attribute
        Then it should be None
        """
        converter = Converter("input.jpg", "output.png")
        assert converter.error is None

    def test_error_attribute_can_be_set(self):
        """
        Scenario: Set error message

        Given a Converter instance
        When the error attribute is set
        Then it should store the error message
        """
        converter = Converter("input.jpg", "output.png")
        converter.error = "Test error message"
        assert converter.error == "Test error message"

    def test_inherits_from_thread(self):
        """
        Scenario: Verify Thread inheritance

        Given a Converter instance
        When checking its type
        Then it should be an instance of Thread
        """
        converter = Converter("input.jpg", "output.png")
        assert isinstance(converter, Thread)

    def test_different_file_paths(self):
        """
        Scenario: Create converter with various file paths

        Given different input and output file paths
        When a Converter is instantiated
        Then it should store both paths correctly
        """
        converter = Converter("/path/to/input.pdf", "/path/to/output.jpg")
        assert converter._infile == "/path/to/input.pdf"
        assert converter._outfile == "/path/to/output.jpg"
