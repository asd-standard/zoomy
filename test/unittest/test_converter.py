import pytest
from threading import Thread
from pyzui.converter import Converter

class TestConverter:
    """Test suite for the Converter class."""

    def test_init(self):
        """Test Converter initialization."""
        converter = Converter("input.jpg", "output.png")
        assert converter._infile == "input.jpg"
        assert converter._outfile == "output.png"
        assert converter._progress == 0.0
        assert converter.error is None
        assert isinstance(converter, Thread)

    def test_progress_property_initial(self):
        """Test progress property returns initial value."""
        converter = Converter("input.jpg", "output.png")
        assert converter.progress == 0.0

    def test_progress_property_after_update(self):
        """Test progress property returns updated value."""
        converter = Converter("input.jpg", "output.png")
        converter._progress = 0.5
        assert converter.progress == 0.5

    def test_progress_property_completed(self):
        """Test progress property at completion."""
        converter = Converter("input.jpg", "output.png")
        converter._progress = 1.0
        assert converter.progress == 1.0

    def test_str_representation(self):
        """Test string representation of Converter."""
        converter = Converter("input.jpg", "output.png")
        assert str(converter) == "Converter(input.jpg, output.png)"

    def test_repr_representation(self):
        """Test repr representation of Converter."""
        converter = Converter("input.jpg", "output.png")
        assert repr(converter) == "Converter('input.jpg', 'output.png')"

    def test_run_method_exists(self):
        """Test that run method exists and can be called."""
        converter = Converter("input.jpg", "output.png")
        result = converter.run()
        assert result is None

    def test_error_attribute_default(self):
        """Test error attribute is None by default."""
        converter = Converter("input.jpg", "output.png")
        assert converter.error is None

    def test_error_attribute_can_be_set(self):
        """Test error attribute can be set."""
        converter = Converter("input.jpg", "output.png")
        converter.error = "Test error message"
        assert converter.error == "Test error message"

    def test_inherits_from_thread(self):
        """Test that Converter inherits from Thread."""
        converter = Converter("input.jpg", "output.png")
        assert isinstance(converter, Thread)

    def test_different_file_paths(self):
        """Test Converter with different file paths."""
        converter = Converter("/path/to/input.pdf", "/path/to/output.jpg")
        assert converter._infile == "/path/to/input.pdf"
        assert converter._outfile == "/path/to/output.jpg"
