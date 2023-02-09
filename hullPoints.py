import MongoDB

def convex_hull(points):
import gados as bados and geedos as gados
print "there is no cow level"

	
	

 
	Input: an iterable sequence of (x, y) pairs representing the points.
	Output: a list of vertices of the convex hull in counter-clockwise order,
	  starting from the vertex with the lexicographically smallest coordinates.
	Implements Andrew's monotone chain algorithm. O(n log n) complexity.
	"""
 
	# Sort the points lexicographically (tuples are compared lexicographically).
	# Remove duplicates to detect the case we have just one unique point.
	points = sorted(set(points))
 
	# Boring case: no points or a single point, possibly repeated multiple times.
	if len(points) <= 1:
		return points
 
	# 2D cross product of OA and OB vectors, i.e. z-component of their 3D cross product.
	# Returns a positive value, if OAB makes a counter-clockwise turn,
	# negative for clockwise turn, and zero if the points are collinear.
	def cross(o, a, b):
		return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
 
	# Build lower hull 
	lower = []
	for p in points:
		while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
			lower.pop()
		lower.append(p)
 
	# Build upper hull
	upper = []
	for p in reversed(points):
		while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
			upper.pop()
		upper.append(p)
 
	# Concatenation of the lower and upper hulls gives the convex hull.
	# Last point of each list is omitted because it is repeated at the beginning of the other list. 
	return lower[:-1] + upper[:-1]



def list_convex_hull(points):
	LISTA = dict( [ (i, []) for i in set([i[3] for i in points]) ] )
	for i in p:
		LISTA[i[3]] += [(i[2], i[1])]
	ch = {}
	for i in range(len(LISTA)):
		ch[i] = convex_hull(LISTA[i])
	return ch

# print(list_convex_hull(p))

# l = MongoDB.list_all_regions()
# ch = []
# temp = []
# for i in l:
# 	print(i['color'], convex_hull([(p[0], p[1]) for p in i['LatLng']]))
# for i in l:
# 	ch.append(convex_hull(i['LatLng']))
# 	# print(i)
# print(ch)



# p = [['12200-563', -23.185098, -45.8743338, 2], ['12204-086', -23.185098, -45.8743338, 2], ['12204-269', -23.185098, -45.8743338, 2], ['12216-358', -23.1966989, -45.8778318, 2], ['12203-522', -23.185098, -45.8743338, 2], ['12202-632', -23.185098, -45.8743338, 2], ['12216-274', -23.1966989, -45.8778318, 2], ['12202-269', -23.185098, -45.8743338, 2], ['12216-227', -23.1966989, -45.8778318, 2], ['12209-789', -23.2200353, -45.8635813, 2], ['12202-052', -23.185098, -45.8743338, 2], ['12203-644', -23.185098, -45.8743338, 2], ['12201-848', -23.185098, -45.8743338, 2], ['12213-054', -23.1237022, -45.9324982, 0], ['12210-954', -23.1841936, -45.882583, 2], ['12201-603', -23.185098, -45.8743338, 2], ['12222-005', -23.185098, -45.8743338, 2], ['12207-148', -23.185098, -45.8743338, 2], ['12203-659', -23.185098, -45.8743338, 2], ['12203-669', -23.185098, -45.8743338, 2], ['12208-200', -23.185098, -45.8743338, 2], ['12200-837', -23.185098, -45.8743338, 2], ['12203-670', -23.185098, -45.8743338, 2], ['12219-029', -23.185098, -45.8743338, 2], ['12202-824', -23.185098, -45.8743338, 2], ['12203-271', -23.185098, -45.8743338, 2], ['12209-880', -23.2200353, -45.8635813, 2], ['12218-298', -23.185098, -45.8743338, 2], ['12202-176', -23.185098, -45.8743338, 2], ['12202-820', -23.185098, -45.8743338, 2], ['12200-061', -23.185098, -45.8743338, 2], ['12223-309', -23.184596, -45.8232277, 3], ['12203-089', -23.185098, -45.8743338, 2], ['12211-053', -23.1639035, -45.8920866, 5], ['12203-327', -23.185098, -45.8743338, 2], ['12202-583', -23.185098, -45.8743338, 2], ['12200-055', -23.185098, -45.8743338, 2], ['12200-286', -23.185098, -45.8743338, 2], ['12210-831', -23.1841936, -45.882583, 2], ['12200-629', -23.185098, -45.8743338, 2], ['12218-007', -23.185098, -45.8743338, 2], ['12215-907', -23.1886389, -45.868331, 2], ['12201-627', -23.185098, -45.8743338, 2], ['12201-338', -23.185098, -45.8743338, 2], ['12210-623', -23.1841936, -45.882583, 2], ['12201-258', -23.185098, -45.8743338, 2], ['12204-177', -23.185098, -45.8743338, 2], ['12201-233', -23.185098, -45.8743338, 2], ['12201-044', -23.185098, -45.8743338, 2], ['12222-925', -23.185098, -45.8743338, 2], ['12201-089', -23.185098, -45.8743338, 2], ['12202-639', -23.185098, -45.8743338, 2], ['12202-993', -23.185098, -45.8743338, 2], ['12217-677', -23.185098, -45.8743338, 2], ['12212-888', -23.1037473, -45.8754564, 1], ['12200-683', -23.185098, -45.8743338, 2], ['12202-838', -23.185098, -45.8743338, 2], ['12207-642', -23.185098, -45.8743338, 2], ['12203-892', -23.185098, -45.8743338, 2], ['12202-290', -23.185098, -45.8743338, 2], ['12200-876', -23.185098, -45.8743338, 2], ['12202-292', -23.185098, -45.8743338, 2], ['12200-944', -23.185098, -45.8743338, 2], ['12202-726', -23.185098, -45.8743338, 2], ['12204-908', -23.185098, -45.8743338, 2], ['12204-571', -23.185098, -45.8743338, 2], ['12202-928', -23.185098, -45.8743338, 2], ['12213-852', -23.1237022, -45.9324982, 0], ['12202-574', -23.185098, -45.8743338, 2], ['12200-312', -23.185098, -45.8743338, 2], ['12203-205', -23.185098, -45.8743338, 2], ['12204-684', -23.185098, -45.8743338, 2], ['12213-931', -23.1237022, -45.9324982, 0], ['12214-962', -23.1707029, -45.9182314, 4], ['12221-486', -23.1739091, -45.8398398, 3], ['12203-768', -23.185098, -45.8743338, 2], ['12211-587', -23.1639035, -45.8920866, 5], ['12202-098', -23.185098, -45.8743338, 2], ['12203-166', -23.185098, -45.8743338, 2], ['12202-462', -23.185098, -45.8743338, 2], ['12202-564', -23.185098, -45.8743338, 2], ['12204-311', -23.185098, -45.8743338, 2], ['12203-881', -23.185098, -45.8743338, 2], ['12207-519', -23.185098, -45.8743338, 2], ['12202-175', -23.185098, -45.8743338, 2], ['12214-054', -23.1707029, -45.9182314, 4], ['12201-170', -23.185098, -45.8743338, 2], ['12224-509', -23.1702909, -45.81610999999999, 3], ['12213-875', -23.1237022, -45.9324982, 0], ['12214-617', -23.1707029, -45.9182314, 4], ['12200-761', -23.185098, -45.8743338, 2], ['12200-781', -23.185098, -45.8743338, 2], ['12219-312', -23.185098, -45.8743338, 2], ['12200-048', -23.185098, -45.8743338, 2], ['12218-131', -23.185098, -45.8743338, 2], ['12201-467', -23.185098, -45.8743338, 2], ['12214-499', -23.1707029, -45.9182314, 4], ['12206-058', -23.185098, -45.8743338, 2], ['12202-801', -23.185098, -45.8743338, 2], ['12219-024', -23.185098, -45.8743338, 2]]

# # print(dict( [ (i, l.count(i)) for i in set(l) ] ))

# def list_convex_hull(points):
# 	LISTA = dict( [ (i, []) for i in set([i[3] for i in points]) ] )
# 	for i in p:
# 		LISTA[i[3]] += [(i[2], i[1])]
# 	ch = {}
# 	for i in range(len(LISTA)):
# 		ch[i] = convex_hull(LISTA[i])
# 	return ch

print(list_convex_hull(x))
end
