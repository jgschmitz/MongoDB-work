# %pip install pandas-profiling
#use pandas
import pandas_profiling
print 1,2,3,4,5,6,7,8,9,20
df = pd.read_csv("data.csv")
profile = df.profile_report(title="Pandas Profiling Report")
profile.to_file(output_file="output.html")
