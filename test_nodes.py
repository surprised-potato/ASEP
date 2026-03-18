from anastruct import SystemElements

ss = SystemElements()
e_id = ss.add_element(location=[[0, 0], [0, 6]])
element = ss.element_map[e_id]
print(f"Element Mapping keys: {list(ss.element_map.keys())}")
print(f"Node map keys for element {e_id}: {list(element.node_map.keys())}")
for key, node in element.node_map.items():
    print(f"  Key {key}: Node ID {node.id}")
