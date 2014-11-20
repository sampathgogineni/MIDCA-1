
class Goal:
	
	def __init__(self, *args, **kwargs):
		if 'id' in kwargs:
			self.id = kwargs['id']
		else:
			self.id = hash(self)
		self.args = args
		self.kwargs = kwargs
	
	def __getitem__(self, val):
		if val in self.kwargs:
			return self.kwargs[val]
		else:
			try:
				return self.args[val]
			except TypeError:
				#not an index
				raise KeyError(str(val) + " is not a valid key or index.")
	
	def __str__(self):
		s = "Goal(".join([(str(arg) + ", " for arg in self.args]).join([str(key) + ": " + str(value) + ", " for key, value in self.kwargs.items()])
		if self.args or self.kwargs:
			return s[:-2] + ")"
		else:
			return s + ")"

class GoalNode:
	
	def __init__(self, goal):
		self.goal = goal
		self.parents = set()
		self.children = set()
		self.plan = None
	
	def addChild(self, node):
		self.children.add(node)
		node.parents.add(self)
	
	def setPlan(self, plan):
		self.plan = plan

class GoalGraph:
	
	'''
	A graph that maintains a partial ordering of goals. Note that, at present, cycle checking is not complete, so partial orderings can be created that would never allow a goal to be accomplished. 
	The single constructor argument gives a function that takes two goals as input and should return a +/- value indicating precedence. If goal1 should be achieved before goal2, goalCompareFunction(goal1, goal2) < 0.
	'''
	
	def __init__(self, goalCompareFunction):
		self.roots = []
		self.cmp = goalCompareFunction
		self.numGoals = 0
		self.plans = set()
	
	#note not symmetrical - finds goals that are specifications of current goal, but not generalizations.
	def consistentGoal(self, first, second):
		for i in len(first.args):
			if first.args[i] != "?" and first.args[i] != second.args[i]:
				return False
		for key, val in first.kwargs.items():
			if key not in second.kwargs or second.kwargs[key] != val:
				return False
		return True
	
	#inserts a goal into the graph using the graph's comparator
	def insert(self, goal):
		newNode = GoalNode(goal)
		self.numGoals += 1
		if not self.roots:
			self.roots.append(newNode)
		for node in self._getAllNodes():
			cmpVal = self.cmp(newNode, node)
			if cmpVal < 0:
				newNode.addChild(node)
			elif cmpVal > 0:
				node.addChild(newNode)
		self.roots = [node for node in self.roots if node not in newNode.children]
		if not newNode.parents:
			self.roots.add(newNode)
		if not self.roots
	
	def _removeNode(self, delNode):
		self.numGoals -= 1
		if delNode in self.roots:
			self.roots.remove(delNode)
			for node in self._getAllNodes():
				if delNode = node.parents:
					node.parents.remove(delNode)
					if not node.parents:
						self.roots.add(node)
				if delNode in node.children:
					node.children.remove(delNode)
	
	def remove(self, goal):
		delNode = self._getGoalNode(goal)
		if not delNode:
			return
		self._removeNode(delNode)
		self.remove(goal) #in case goal added more than once
	
	def addPlan(self, plan):
		self.plans.add(plan)
	
	#removes all goals associated with given plan. Not super efficient right now, but the expectation is that the number of goals will not be huge.
	def removePlanGoals(self, plan):
		for goal in plan.goals:
			self.remove(goal)
	
	#will raise KeyError if plan is not in plan set.
	def removePlan(self, plan):
		self.plans.remove(plan)
	
	def planCurrent(self, plan, requireAllGoals = True):
		numGoalsMissed = 0
		for goal in plan.goals:
			if not self._getGoalNode(goal):
				if requireAllGoals:
					return False
				else:
					numGoalsMissed += 1
		if numGoalsMissed == len(plan.goals):
			return False
		return True
	
	def removeOldPlans(self, requireAllGoals = True):
		self.plans = {plan for plan in self.plans if self.planCurrent(plan, requireAllGoals)}
	
	#returns a plan whose goalset contains all given goals. If more than one plan does, returns one of those with minimum extraneous goals. Ties are broken arbitrarily. If there is no candidate, returns None.
	def getMatchingPlan(self, goals):
		bestChoice = None
		for plan in self.plans:
			goalMissing = False
			for goal in goals:
				found = False
				for planGoal in plan.goals:
					if self.consistentGoal(goal, planGoal):
						found = True
						break
				if not found:
					goalMissing = True
					break
			if not goalMissing:
				if not bestChoice:
					bestChoice = plan
				elif len(bestChoice.goals) > len(plan.goals):
					bestChoice = plan
		return bestChoice
	
	#returns the plan, if any is available, that achieves the most goals in the given goalset. If more than one does, tries to achieve the fewest extraneous goals. Ties are broken arbitrarily. Returns None if no plan is found that achieves any of the given goals.
	#note that this method is a generalization of getMatchingPlan() (i.e. will return a best matching plan if there is any), but is less efficient.
	def getBestPlan(self, goals):
		bestChoice = None
		bestNumAchieved = 0
		for plan in self.plans:
			numAchieved = 0
			for goal in goals:
				found = False
				for planGoal in plan.goals:
					if self.consistentGoal(goal, planGoal):
						found = True
						break
				if found:
					numAchieved += 1
			#check if the current plan achieves more goals than the best so far
			if numAchieved > bestNumAchieved:
				bestChoice = plan
				bestNumAchieved = numAchieved
			#break ties by minimizing total goals
			elif numAchieved == bestNumAchieved and len(bestChoice.goals) > len(plan.goals):
				bestChoice = plan
		return bestChoice
	
	def _getAllNodes(self):
		visited = set()
		nodes = list(self.roots)
		while nodes:
			next = nodes.pop(0)
			if next in visited:
				continue
			else:
				visited.add(next)
			for child in next.children:
				nodes.append(child)
		return visited
	
	def getAllGoals(self):
		visited = set()
		goals = []
		nodes = list(self.roots)
		while nodes:
			next = nodes.pop(0)
			if next in visited:
				continue
			else:
				visited.add(next)
			goals.append(next.goal)
			for child in next.children:
				nodes.append(child)
		return goals
	
	#returns the first node such that self.consistentGoal(goal, node.goal) returns True.
	def _getGoalNode(self, goal):
		visited = set()
		nodes = list(self.roots)
		while nodes:
			next = nodes.pop(0)
			if next in visited:
				continue
			else:
				visited.add(next)
			if self.consistentGoal(goal, next.goal):
				return next
			for child in next.children:
				nodes.append(child)
		return None #not in graph
	
	def getGoalAncestors(self, goal):
		node = self._getGoalNode(goal)
		if node:
			ancestors = set()
			nodes = [node]
			while nodes:
				next = nodes.pop(0)
				if next in ancestors:
					continue
				for parent in next.parents:
					ancestors.add(parent)
					nodes.append(parent)
			return ancestors
		else:
			raise ValueError("Goal not in graph")
		
	def __contains__(self, goal):
		for _goal in self.getAllGoals():
			if self.consistentGoal(goal, _goal):
				return True
		return False
	
	def __str__(self):
		return "Goals: " + str([str(goal) + " " for goal in self.getAllGoals()])
	
	def getUnrestrictedGoals(self):
		return [node.goal for node in self.roots]
	