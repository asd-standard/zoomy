.. PyZUI project structure file

Reading Documentation
=====================

This guide explains the documentation conventions used throughout the PyZUI codebase.

Docstring Format
----------------

Every class and method (both public and private) in PyZUI includes comprehensive docstrings following a consistent format. Understanding this format will help you navigate the API documentation effectively.

Constructor/Method Signature
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each docstring begins with the calling signature::

    Constructor:
        ClassName(param1, param2, ...)

    Method:
        method_name(param1, param2, ...)

    Function:
        function_name(param1, param2, ...)

This shows how to properly call the method or initialize the class.

Parameters Section
~~~~~~~~~~~~~~~~~~

The parameters are documented with their types::

    Parameters:
        param1 : type
            Description of param1
        param2 : type
            Description of param2

**Type annotations** indicate the expected data type for each parameter. Ensure your arguments match these types when calling methods or instantiating classes.

Return Type
~~~~~~~~~~~

The return type is documented in the following format::

    Returns:
        return_type
            Description of the return value

Or using the shorthand notation::

    ClassName(param1, param2, ...) --> return_type

This indicates the type returned by the method or constructor.

Example Docstring
~~~~~~~~~~~~~~~~~

Here's a complete example of how docstrings are structured in PyZUI::

    class TileManager:
        """
        Constructor:
            TileManager(cache_size, auto_cleanup)

        Parameters:
            cache_size : int
                Maximum number of tiles to cache in memory
            auto_cleanup : bool
                Enable automatic cleanup of old tiles

        TileManager(cache_size, auto_cleanup) --> TileManager

        Manages tile caching and retrieval for the PyZUI system.
        Coordinates between tile providers and maintains a two-tier
        cache for optimal performance.
        """

Reading Tips
~~~~~~~~~~~~

When browsing the API documentation:

1. **Start with the class overview** - Read the class docstring to understand its purpose
2. **Check the constructor** - See what parameters are needed to instantiate the class
3. **Review public methods** - Look for methods without underscore prefixes
4. **Note parameter types** - Ensure you pass the correct types to avoid runtime errors
5. **Understand return values** - Know what each method returns for proper usage

**Note:** Private methods (prefixed with ``_`` or ``__``) are documented for developer reference but should not be called directly in normal usage.





