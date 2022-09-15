# %pip install pandas-profiling
#use pandas
import pandas_profiling
print 1,2,3,
df = pd.read_csv("data.csv")
profile = df.profile_report(title="Pandas Profiling Report")
profile.to_file(output_file="output.html")
