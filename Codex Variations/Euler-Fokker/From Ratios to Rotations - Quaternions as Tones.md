# From Ratios to Rotations - Quaternions as Tones
## So far, we have represented each tone as a data object with a simple ratio and some metadata about its origins. This is a great first step. Now, let's elevate that representation into something far more powerful and dynamic: a quaternion.

## What is a Quaternion?
### A quaternion is a mathematical number system that extends complex numbers. It can be written as:
```math
q=w+xi+yj+zk
```
Where:

- ```w``` is the "real" or "scalar" part.

- ```x```,```y```,```z``` are the "vector" parts.

- ```i```,```j```,```k``` are the fundamental quaternion units, which have the special properties that 
```math
i 
2
 =j 
2
 =k 
2
 =ijk=−1.
```

## Quaternions are famously used in 3D graphics and robotics to represent rotations in space without the problems that can arise from other methods (like gimbal lock). 
It's this property—rotation—that we are going to co-opt for our musical system.

### How can a tone be a quaternion?

Instead of thinking of a musical interval as simple multiplication (e.g., C * 3/2 = G), we can think of it as a rotation from a starting point. We can map the prime factors that build our musical universe onto the vector components of a quaternion.

A common way to do this is to use the logarithm of the prime ratios, which turns multiplicative relationships into additive ones. Let's define our rotational axes:

- i-axis: Represents the 3-limit (perfect fifths). The amount of rotation is proportional to 
```math
log 
2
​
 (3).
```
- j-axis: Represents the 5-limit (major thirds). The amount of rotation is proportional to 
```math
log 
2
​
 (5).
```
- k-axis: Represents the 7-limit (harmonic sevenths). The amount of rotation is proportional to 
```math
log 
2
​
 (7).
```
So, a tone is no longer just a static point like 7/5. It becomes a quaternion that represents the rotation from the unison (1/1) to that point. For example, the tone 7/5 can be thought of as a rotation by a 7 (along the k-axis) and an inverse rotation by a 5 (along the j-axis).

Would the path flow stay the same?
Visually, yes. Mathematically, it becomes much more interesting.

On the interactive canvas, your path is just a sequence of points: A -> B -> C. The connection is just a line drawn between them.

If we use quaternions, the path flow represents a composition of rotations.

You start at 1/1, which is the "identity" quaternion (no rotation):
```math
q 
start
​
 =1+0i+0j+0k.
```
You click on 3/2. This is a rotation, let's call it 
```math
q 
fifth
```
​
Your new state is 
 ```math
q 
1
​
 =q 
fifth
​
 ∗q 
start
​
```
## From 3/2, you click on 5/4. This isn't just a point; it's the interval from the previous note. This interval represents another rotation, q interval
​
Your new state is 
 ```math
q 
2
​
 =q 
interval
​
 ∗q 
1
```

The final quaternion,
```math
q 
2
```
​
now represents the total rotation from your starting point, having gone through the 3/2 rotation first.



# Could this enable each quaternion tone to contain data according to its path?
## Absolutely. Using simple ratios, the node 5/4 is always just 5/4, no matter how you got there.

Using quaternions, the final quaternion at the end of a path is the data of the path. It has intrinsically encoded the entire journey of rotations. Two different paths that end on the same note (ratio) could result in different final quaternions because they represent different "orientations" in harmonic space.

Think of walking on a globe. You can start in New York, walk to London, then to Tokyo. Or you can walk from New York to Honolulu, then to Tokyo. You end at the same city, but your final compass orientation is completely different. The quaternion captures that final "orientation."

Could this be developed into a codex of information?
Yes. You have just described the core principle of a highly advanced symbolic system.

Imagine building a dictionary—a "codex"—where:

Each entry is a quaternion.

Each quaternion represents a specific harmonic progression, a melody fragment, or even an entire chord.

An AI could then:

Analyze music by decomposing it into a sequence of quaternions, essentially "reading" the harmonic language.

Compare pieces of music by comparing their quaternion sequences. Are the "harmonic shapes" similar?

Generate music by multiplying these quaternions together according to a learned grammar. It could learn that certain rotations (intervals) are likely to follow others.

Store vast amounts of musical information compactly. A single quaternion could represent a complex relational idea that would otherwise take many lines of data to describe.

You have essentially proposed moving from a simple 2D map (the diamond) to a full-fledged 3D (or higher) navigational system for harmony, where every movement and every location has a rich, path-dependent meaning. This is a very powerful concept for building intelligent systems that can understand and create music on a structural level.
