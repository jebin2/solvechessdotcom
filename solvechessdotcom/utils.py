from lxml import etree

def chess_position(svg_path):
    tree = etree.parse(svg_path)
    root = tree.getroot()
    namespaces = {'svg': 'http://www.w3.org/2000/svg'}
    g_element = root.find('.//svg:g[@id="current_move"]', namespaces=namespaces)
    if g_element is None:
        return (0, 0)
    point_str = g_element.get("piece_point")
    if not point_str:
        return (0, 0)
    points = tuple(map(float, point_str.split(",")))
    return (int(points[0])+420, int(points[1]))