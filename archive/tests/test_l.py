from anastruct import SystemElements
ss = SystemElements()
ss.add_truss_element(location=[[0, 0], [3, 4]])
print(ss.element_map[1].l)
