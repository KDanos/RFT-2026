from src.rft_app.project import ColumnSpec, ProjectDataManager
import pandas as pd

m = ProjectDataManager()
specs = [ColumnSpec("P","pressure", "Pa")]
df = pd.DataFrame({"P":[1.0,2.0]})
print (m.add_dataframe(df,specs))