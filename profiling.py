# %pip install pandas-profiling
#use pandas
import pandas_profiling

df = pd.read_csv("data.csv")
profile = df.profile_report(title="Pandas Profiling Report")
profile.to_file(output_file="output.html")
