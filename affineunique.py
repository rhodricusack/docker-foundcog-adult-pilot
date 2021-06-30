import numpy as np

a=np.array([1,2,3,4])
b=np.array([1,2,5,6])
c=np.array([2,2,5,6])
allaffines=np.vstack([b,a,b,a,b,c])


print(allaffines)
urows=np.unique(allaffines, axis=0, return_inverse=True, return_counts=True)
print(urows)
maxcount = np.argmax(urows[2])
print(maxcount)
