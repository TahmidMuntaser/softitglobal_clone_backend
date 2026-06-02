def sort_operations(endpoint):
    path, _path_regex, method, _callback = endpoint

    ordered_paths = [
        '/api/categories/',
        '/api/products/',
        '/api/products/{id}/',
        '/api/cart/add/',
        '/api/cart/',
        '/api/cart/item/{id}/',
        '/api/checkout/',
        '/api/orders/{id}/',
    ]

    ordered_methods = ['GET', 'POST', 'PATCH', 'DELETE']

    try:
        path_index = ordered_paths.index(path)
    except ValueError:
        path_index = len(ordered_paths)

    try:
        method_index = ordered_methods.index(method)
    except ValueError:
        method_index = len(ordered_methods)

    return path_index, method_index, path, method
