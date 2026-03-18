from anastruct import SystemElements
ss = SystemElements()
nid = ss.add_truss_element(location=[[0,0], [1,0]])
ss.add_support_hinged(node_id=1)
ss.solve()
node = ss.node_map[1]
print("Node attributes:", dir(node))
try:
    print("Node FY Reaction:", node.reaction_force)
except AttributeError:
    print("Node has no reaction_force attribute")
