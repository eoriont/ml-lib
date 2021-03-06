from os import name
import random

class DataFrame:
    def __init__(self, data_dict, columns=None):
        self.data_dict = data_dict
        self.columns = list(data_dict) if columns is None else columns

    def to_array(self):
        if self.columns[0] in self.data_dict:
            arrs = [self.data_dict[col] for col in self.columns]
            return [list(arr) for arr in zip(*arrs)]
        else:
            return []

    def append_pairwise_interactions(self):
        columns_to_multiply = self.cartesian_product()
        d, c = self.get_data_copies()
        for x in columns_to_multiply:
            new_col = '_'.join(x)
            c.append(new_col)
            d[new_col] = [x*y for x, y in zip(d[x[0]], d[x[1]])]
        return DataFrame(d, c)

    def cartesian_product(self):
        l = []
        for x in self.columns:
            for y in self.columns:
                if x != y and (y, x) not in l:
                    l.append((x, y))
        return l

    @classmethod
    def from_array(cls, arr, columns):
        return cls({c: list(a) for c, a in zip(columns, zip(*arr))}, columns)

    def filter_columns(self, cols):
        return DataFrame(self.data_dict, cols)

    def include_column(self, col):
        d, c = self.get_data_copies()
        return DataFrame(d, c+[col])

    def get_data_copies(self):
        return {k: v.copy() for k, v in self.data_dict.items()}, self.columns.copy()

    def create_all_dummy_variables(self):
        categorical_cols = [col for col in self.data_dict if any(
            isinstance(i, str) for i in self.data_dict[col])]
        list_categorical_cols = [col for col in self.data_dict if any(
            isinstance(i, list) for i in self.data_dict[col])]
        df = self
        for col in categorical_cols:
            df = df.create_string_dummy_variables(col)
        for col in list_categorical_cols:
            df = df.create_list_dummy_variables(col)
        return df

    def create_string_dummy_variables(self, col):
        d, c = self.get_data_copies()
        col_data = []
        [col_data.append(i) for i in d[col] if i not in col_data]
        new_cols = [f"{col}_{name}" for name in col_data]
        new_data = [[(1 if i == item else 0)
                     for i in d[col]] for item in col_data]
        new_cols_data = dict(zip(new_cols, new_data))
        del d[col]
        d.update(new_cols_data)
        c.remove(col)
        c += new_cols
        return DataFrame(d, c)

    def create_list_dummy_variables(self, col):
        d, c = self.get_data_copies()
        col_data = []
        for arr in d[col]:
            for x in arr:
                if x not in col_data:
                    col_data.append(x)
        new_data = [[(1 if item in arr else 0) for arr in d[col]]
                    for item in col_data]
        new_cols_data = dict(zip(col_data, new_data))
        del d[col]
        d.update(new_cols_data)
        c.remove(col)
        c += col_data
        return DataFrame(d, c)

    def remove_columns(self, cols):
        d, c = self.get_data_copies()
        for col in cols:
            c.remove(col)
            del d[col]
        return DataFrame(d, c)

    def append_columns(self, data_dict, column_order=None):
        d, c = self.get_data_copies()
        d.update(data_dict)
        c += list(data_dict) if column_order is None else column_order
        return DataFrame(d, c)

    def apply(self, column, func):
        d, c = self.get_data_copies()
        d[column] = [func(x) for x in d[column]]
        return DataFrame(d, c)

    def apply_new(self, column, new_col, func):
        d, c = self.get_data_copies()
        d[new_col] = [func(x) for x in d[column]]
        return DataFrame(d, c+[new_col])


    # This is the same as filter_columns
    def select(self, cols):
        return DataFrame(self.data_dict, cols)

    def select_rows(self, rows):
        arr = self.to_array()
        return DataFrame.from_array((x for i, x in enumerate(arr) if i in rows), self.columns)

    def where(self, func):
        arr = self.to_array()
        return DataFrame.from_array((x for x in arr if func(self.to_entry(x))), self.columns)

    def to_entry(self, arr):
        return {k: v for k, v in zip(self.columns, arr)}

    def add_entry(self, entry):
        d, c = self.get_data_copies()
        for col in c:
            d[col].append(entry[col])
        return DataFrame(d, c)

    def order_by(self, col, ascending=True):
        return DataFrame.from_array(sorted(
            self.to_array(),
            key=lambda x: x[self.columns.index(col)],
            reverse=not ascending
        ), self.columns)

    def get_column(self, col):
        if col in self.columns:
            if col in self.data_dict.keys():
                return self.data_dict[col].copy()
            else:
                return []
        else:
            raise Exception("Accessing column that doesn't exist!")

    def __len__(self):
        try:
            return len(next(iter(self.data_dict.values())))
        except StopIteration:
            return 0

    def remove_entry(self, index):
        d, c = self.get_data_copies()
        entry = {}
        for col in c:
            entry[col] = d[col][index]
            del d[col][index]
        return DataFrame(d, c), entry

    def to_json(self):
        return [self.to_entry(arr) for arr in self.to_array()]

    def remove_duplicates(self, col):
        indices = []
        checked = []
        for i, x in enumerate(self.data_dict[col]):
            if x not in checked:
                checked.append(x)
                indices.append(i)
        return self.select_rows(indices)

    def round_column(self, col, places):
        d, c = self.get_data_copies()
        for i, x in enumerate(d[col]):
            d[col][i] = round(x, places)
        return DataFrame(d, c)

    def random_row(self):
        return random.choice(self.to_array())

    @classmethod
    def from_csv(cls, path_to_csv, data_types, parser):
        with open(path_to_csv, "r") as file:
            s = file.read().split("\n")
            # head = parser(s[0])
            data = [[None if val.strip() == "" else t(val.strip()) for t, val in zip(data_types.values(), parser(x))] for x in s[1:] if x.strip() != ""]
            return cls.from_array(data, list(data_types.keys()))

    def min(self, col):
        return min(self.data_dict[col])

    def max(self, col):
        return max(self.data_dict[col])

    def save_csv(self, path_to_csv):
        with open(path_to_csv, "w") as file:
            for i, col in enumerate(self.columns):
                file.write(str(col))
                if i+1 < len(self.columns):
                    file.write(",")
            file.write("\n")
            for row in self.to_array():
                for i, val in enumerate(row):
                    file.write(str(val))
                    if i+1 < len(row):
                        file.write(",")
                file.write("\n")

    # Bad bad bad bad
    def group_by(self, column):
        names = []
        new_rows = []
        for i, x in enumerate(self.get_column(column)):
            if x not in names:
                names.append(x)
                new_rows.append([])
            new_rows[names.index(x)].append(i)

        x = [[[y for j, y in enumerate(self.get_column(col)) if j in new_rows[i]] if col != column else names[i] for col in self.columns] for i in range(len(names))]
        return DataFrame.from_array(x, self.columns)

    def aggregate(self, col, method):
        d, c = self.get_data_copies()
        d[method+col] = [DataFrame.get_methods()[method](x) for x in self.get_column(col)]
        return DataFrame(d, c)

    @staticmethod
    def get_methods():
        return {
            'count': lambda x: len(x),
            'max': lambda x: max(x),
            'min': lambda x: min(x),
            'sum': lambda x: sum(x),
            'avg': lambda x: sum(x)/len(x)
        }

    def query(self, query):
        tokens = query.split(" ")

        todo = {'select': [], 'order': []}
        i = iter(tokens)
        for t in i:
            if t == "SELECT":
                while True:
                    x = next(i)
                    todo["select"].append(x.strip(","))
                    if x[-1] != ",": break
            elif t == "ORDER":
                by = next(i)
                if by == "BY":
                    while True:
                        col = next(i)
                        way = next(i)
                        todo["order"].append((col, way.strip(",")=="ASC"))
                        if way[-1] != ",": break
        d, c = self.get_data_copies()
        df = DataFrame(d, c)
        for x, y in reversed(todo["order"]):
            df = df.order_by(x, y)
        df = df.select(todo["select"])
        return df




if __name__ == "__main__":
    df = DataFrame.from_array(
        [['Kevin', 'Fray', 5],
        ['Charles', 'Trapp', 17],
        ['Anna', 'Smith', 13],
        ['Sylvia', 'Mendez', 9]],
        columns = ['firstname', 'lastname', 'age']
    )

    # print(df.query("SELECT lastname, firstname, age ORDER BY age DESC").to_array())
    # print(df.query("SELECT firstname ORDER BY lastname ASC").to_array())
    df = DataFrame.from_array(
        [['Kevin', 'Fray', 5],
        ['Melvin', 'Fray', 5],
        ['Charles', 'Trapp', 17],
        ['Carl', 'Trapp', 17],
        ['Anna', 'Smith', 13],
        ['Hannah', 'Smith', 13],
        ['Sylvia', 'Mendez', 9],
        ['Cynthia', 'Mendez', 9]],
        columns = ['firstname', 'lastname', 'age']
    )
    print(df.query("SELECT lastname, firstname, age ORDER BY age ASC, firstname DESC").to_array())
