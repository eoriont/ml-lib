import sys, random, math
sys.path.append('src/models')
from decision_tree_node import DecisionTreeNode

class DecisionTree:
    def __init__(self, split_metric="gini", dependent_variable="class", max_depth=None, training_percentage=1):
        self.max_depth = max_depth
        self.dependent_variable = dependent_variable
        self.split_metric = split_metric
        self.training_percentage = training_percentage

    def split(self):
        return self.root.split(self.split_metric)

    def fit(self, df):
        df = df.append_columns({
                'id': [i for i in range(len(df))]
            })
        if self.training_percentage < 1:
            df = df.select_rows(
                [random.randint(0, len(df))
                    for _ in range(math.floor(len(df) * self.training_percentage))]
            )
        self.root = DecisionTreeNode(df, self.dependent_variable, max_depth=self.max_depth)
        while self.split():
            pass

    def classify(self, obs):
        return self.root.classify(obs)

    def predict(self, obs):
        return self.classify(obs)
