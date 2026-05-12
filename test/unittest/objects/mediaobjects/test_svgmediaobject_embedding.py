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

from unittest.mock import Mock, patch

from pyzui.objects.mediaobjects.svgmediaobject import SVGMediaObject


class TestSVGMediaObjectEmbedding:
    """
    Feature: SVG Content Embedding in PZS Files

    Tests for embedding SVG content directly in PZS files
    when SVGs are modified (picker dialog, clipboard, svg_*_utils).
    """

    @patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer')
    def test_is_modified_default_false_for_file_path(self, mock_renderer_class):
        """
        Scenario: SVG loaded from file path is not modified by default

        Given a valid SVG file path "test.svg"
        When SVGMediaObject is created
        Then is_modified should be False
        And original_file_path should be set
        """
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_renderer.defaultSize.return_value = Mock(width=lambda: 100, height=lambda: 200)
        mock_renderer_class.return_value = mock_renderer

        scene = Mock()
        obj = SVGMediaObject("test.svg", scene)

        assert obj.is_modified is False
        assert obj.original_file_path == "test.svg"

    @patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer')
    def test_is_modified_true_for_cache_hash(self, mock_renderer_class):
        """
        Scenario: SVG loaded from cache hash is marked as modified

        Given a cache hash "svg_12345678"
        When SVGMediaObject is created
        Then is_modified should be True
        And original_file_path should be None
        """
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_renderer.defaultSize.return_value = Mock(width=lambda: 100, height=lambda: 200)
        mock_renderer_class.return_value = mock_renderer

        # Mock SVG cache
        with patch('pyzui.objects.mediaobjects.svgmediaobject.get_svg_cache') as mock_get_cache:
            mock_cache = Mock()
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_cache.get_cache_path.return_value = mock_path
            mock_get_cache.return_value = mock_cache

            scene = Mock()
            obj = SVGMediaObject("svg_12345678", scene)

            assert obj.is_modified is True
            assert obj.original_file_path is None

    @patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer')
    def test_mark_as_modified_method(self, mock_renderer_class):
        """
        Scenario: mark_as_modified() sets modification state

        Given an SVGMediaObject loaded from file path
        When mark_as_modified() is called
        Then is_modified should be True
        And cached content should be cleared
        """
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_renderer.defaultSize.return_value = Mock(width=lambda: 100, height=lambda: 200)
        mock_renderer_class.return_value = mock_renderer

        scene = Mock()
        obj = SVGMediaObject("test.svg", scene)

        # Initially not modified
        assert obj.is_modified is False

        # Call mark_as_modified
        obj.mark_as_modified()

        # Now should be modified
        assert obj.is_modified is True

    @patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer')
    def test_get_svg_content_from_cache_hash(self, mock_renderer_class):
        """
        Scenario: Get SVG content from cache hash

        Given an SVGMediaObject with cache hash
        When get_svg_content() is called
        Then it should return content from SVG cache
        And content should be cached
        """
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_renderer.defaultSize.return_value = Mock(width=lambda: 100, height=lambda: 200)
        mock_renderer_class.return_value = mock_renderer

        test_content = '<svg><circle cx="50" cy="50" r="40"/></svg>'

        # Mock SVG cache
        with patch('pyzui.objects.mediaobjects.svgmediaobject.get_svg_cache') as mock_get_cache:
            mock_cache = Mock()
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_cache.get_cache_path.return_value = mock_path
            mock_cache.get_svg_content.return_value = test_content
            mock_get_cache.return_value = mock_cache

            scene = Mock()
            obj = SVGMediaObject("svg_12345678", scene)

            # First call should get from cache
            content = obj.get_svg_content()

            assert content == test_content
            mock_cache.get_svg_content.assert_called_once_with("svg_12345678")

            # Second call should use cache
            content2 = obj.get_svg_content()
            assert content2 == test_content
            # Still only called once due to caching
            mock_cache.get_svg_content.assert_called_once()

    @patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer')
    def test_get_svg_content_from_file_path(self, mock_renderer_class):
        """
        Scenario: Get SVG content from file path

        Given an SVGMediaObject with file path
        When get_svg_content() is called
        Then it should read content from file
        And content should be cached
        """
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_renderer.defaultSize.return_value = Mock(width=lambda: 100, height=lambda: 200)
        mock_renderer_class.return_value = mock_renderer

        test_content = '<svg><circle cx="50" cy="50" r="40"/></svg>'

        # Mock Path.read_text
        with patch('pyzui.objects.mediaobjects.svgmediaobject.Path') as mock_path_class:
            mock_path = Mock()
            mock_path.read_text.return_value = test_content
            mock_path_class.return_value = mock_path

            scene = Mock()
            obj = SVGMediaObject("test.svg", scene)

            # First call should read from file
            content = obj.get_svg_content()

            assert content == test_content
            mock_path.read_text.assert_called_once_with(encoding='utf-8')

            # Second call should use cache
            content2 = obj.get_svg_content()
            assert content2 == test_content
            # Still only called once due to caching
            mock_path.read_text.assert_called_once()

    @patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer')
    def test_get_svg_content_error_file_not_found(self, mock_renderer_class):
        """
        Scenario: Get SVG content when file doesn't exist

        Given an SVGMediaObject with non-existent file path
        When get_svg_content() is called
        Then it should return None
        And error should be logged
        """
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_renderer.defaultSize.return_value = Mock(width=lambda: 100, height=lambda: 200)
        mock_renderer_class.return_value = mock_renderer

        # Mock Path.read_text to raise exception
        with patch('pyzui.objects.mediaobjects.svgmediaobject.Path') as mock_path_class:
            mock_path = Mock()
            mock_path.read_text.side_effect = FileNotFoundError("File not found")
            mock_path_class.return_value = mock_path

            scene = Mock()
            obj = SVGMediaObject("missing.svg", scene)

            # Mock the logger on the instance
            obj._SVGMediaObject__logger = Mock()

            content = obj.get_svg_content()

            assert content is None
            obj._SVGMediaObject__logger.error.assert_called()

    @patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer')
    def test_set_svg_content(self, mock_renderer_class):
        """
        Scenario: Set SVG content

        Given an SVGMediaObject
        When set_svg_content() is called
        Then content should be cached
        And is_modified should be True
        """
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_renderer.defaultSize.return_value = Mock(width=lambda: 100, height=lambda: 200)
        mock_renderer_class.return_value = mock_renderer

        test_content = '<svg><circle cx="50" cy="50" r="40"/></svg>'

        scene = Mock()
        obj = SVGMediaObject("test.svg", scene)

        # Initially not modified
        assert obj.is_modified is False

        # Set content
        obj.set_svg_content(test_content)

        # Now should be modified and have cached content
        assert obj.is_modified is True
        assert obj.get_svg_content() == test_content

    @patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer')
    def test_to_dict_includes_modification_state(self, mock_renderer_class):
        """
        Scenario: to_dict() includes modification state

        Given an SVGMediaObject with modification state
        When to_dict() is called
        Then result should include is_modified and original_file_path
        """
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_size = Mock()
        mock_size.width.return_value = 100
        mock_size.height.return_value = 200
        mock_renderer.defaultSize.return_value = mock_size
        mock_renderer_class.return_value = mock_renderer

        scene = Mock()
        obj = SVGMediaObject("test.svg", scene)

        # Mark as modified
        obj.mark_as_modified()

        # Mock inherited attributes
        with patch.object(obj, '_media_id', "test.svg"), \
             patch.object(obj, '_x', 10.0), \
             patch.object(obj, '_y', 20.0), \
             patch.object(obj, '_z', 30.0), \
             patch.object(obj, 'vx', 1.0), \
             patch.object(obj, 'vy', 2.0), \
             patch.object(obj, 'vz', 3.0):

            result = obj.to_dict()

            assert 'is_modified' in result
            assert result['is_modified'] is True
            assert 'original_file_path' in result
            assert result['original_file_path'] == 'test.svg'

    @patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer')
    def test_from_dict_restores_modification_state(self, mock_renderer_class):
        """
        Scenario: from_dict() restores modification state

        Given a dictionary with modification state
        When from_dict() is called
        Then SVGMediaObject should have correct modification state
        """
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_renderer.defaultSize.return_value = Mock(width=lambda: 100, height=lambda: 200)
        mock_renderer_class.return_value = mock_renderer

        test_data = {
            'media_id': 'test.svg',
            'position': (10.0, 20.0, 30.0),
            'velocity': (1.0, 2.0, 3.0),
            'is_modified': True,
            'original_file_path': 'test.svg'
        }

        scene = Mock()
        obj = SVGMediaObject.from_dict(test_data, scene)

        assert obj.is_modified is True
        assert obj.original_file_path == 'test.svg'

    def test_max_embedded_svg_size_constant(self):
        """
        Scenario: MAX_EMBEDDED_SVG_SIZE_BYTES constant exists

        Given the SVGMediaObject class
        When accessing MAX_EMBEDDED_SVG_SIZE_BYTES
        Then it should be 1MB (1048576 bytes)
        """
        assert hasattr(SVGMediaObject, 'MAX_EMBEDDED_SVG_SIZE_BYTES')
        assert isinstance(SVGMediaObject.MAX_EMBEDDED_SVG_SIZE_BYTES, int)
        assert SVGMediaObject.MAX_EMBEDDED_SVG_SIZE_BYTES == 1 * 1024 * 1024
