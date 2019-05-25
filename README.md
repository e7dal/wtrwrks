# Waterworks and Transforms
When starting a new project, a datascientist or machine learning engineer spends a large portion, if not a majority of their time preparing the data for input into some ML algorithm. This involves cleaning, transforming and normalizing a variety of different data types so that they can all be represented as some set of well behaved vectors (or more generally some higher dimensional tensor). These transformations are usually quite lossy since much of the information contained in the raw data is unhelpful for prediction. This, however, has the unfortunate side effect that it makes it impossible to reconstruct the original raw data from its transformed counterpart, which is a helpful if not necessary ability in many situations. 

Being able to look at the data in it's original form rather than a large block of numbers makes debugging process smoother and the model diagnosing more intuitive. That was the original motivation for creating this package but this system can be used in a wide variety of situations outsie of ML pipelines and was set up in as general purpose of a way as possible. That being said, there is submodule called 'Transforms' which is build on top of the waterworks system that is specifically for ML pipelines. These transforms convert categorical, numerical, datetime and string datatype into vectorized inputs for ML pipelines. This is discussed further [below](*ml-transfoms)

# Waterworks
## 'Theory' of Waterworks
Creating a 'waterwork' amounts to creating a reversible function, i.e. a function f such that for any a &in; dom(f) you have an f<sup>-1</sup> such that f<sup>-1</sup>(f(a)) = a. Note that this does not imply that this same function f will satisfy f(f<sup>-1</sup>(b)) = b, for any b since f need only be injective not isomorphic. Waterworks are built from smaller reversible operations (called tanks) and are attached together to get more complex operations. Anyone who has built anything using [tensorflow](https://www.tensorflow.org/) will quickly see where the idea for this method of defining waterworks came from. A waterwork is a directed acyclic graph describing a series of operations to perform. The nodes of this graph are the tanks (i.e. operations) and the edges are the tubes/slots. The tanks are themselves reversible, and thus the entire waterwork is reversible. 

As the reader is quickly finding out, there is a fair amount of made up jargon that the author found difficult to avoid. But hopefully the metaphor makes it a little bit easier to digest. Reference this diagram for a more intuitive picture of what is going on.
<img src="https://raw.githubusercontent.com/CRSilkworth/waterworks/master/images/waterwork.png" alt="drawing" width="600"/>)

Basically, you build a waterwork by connecting tanks together by fitting tubes into slots. The end result it a collection of connected tanks with some slots and tubes left unconnected. These are the inputs and outputs of the function (waterwork) and are known as funnels and taps respectively. 

## Examples
### Example 1
As a concrete example take the function f(a, b, c) = (a + b) * c. Let's imagine we wanted to build a waterwork that simulates this function. Because addition and multiplication are both actually quite lossy, there is a fair amount of additional information that you need to carry around in order to reconstruct a, b, and c later on. Both addition and multiplication store either the first (slot 'a') or second (slot 'b') input, depending on whichever has a fewer number of elemements. One can see this full process in action by running the code:
```python
from waterworks import Waterwork, add, mul
import pprint

with Waterwork() as ww:
  add_tubes, add_slots = add([1., 2., 3.], [3., 4., 5.])
  mul_tubes, mul_slots = mul(add_tubes['target'], [2., 2., 2.])

taps = ww.pour(key_type='str')
pprint.pprint(taps)
```
```
{'Add_0/tubes/a_is_smaller': False,
 'Add_0/tubes/smaller_size_array': array([3., 4., 5.]),
 'Mul_0/tubes/a_is_smaller': False,
 'Mul_0/tubes/missing_vals': array([], dtype=float64),
 'Mul_0/tubes/smaller_size_array': array([2., 2., 2.]),
 'Mul_0/tubes/target': array([ 8., 12., 16.])}
```

Normally, when one wants to do to run (a + b) * c, you get a single output. However, in order to make this reversible, a 6 different outputs are returned. However, with these outputs one is able to completely undo the (a + b) * c operation, even in the presence of zeros, to get back the original a, b and c. 

The taps, are all the tubes from all the tanks that were not connected to some other slot. Hence, 'add_tubes\["target"\]', does not appear as a tap since it was connected to the mul_slots\['a'\]. 

Taking these tap values and feeding them to pump, you can get back a, b and c:
```python
funnels = ww.pump(taps, key_type='str')
```
```
{'Add_0/slots/a': array([1., 2., 3.]),
 'Add_0/slots/b': array([3., 4., 5.]),
 'Mul_0/slots/b': array([2., 2., 2.])}
 ```
 ### Example 2
In the previous example, all funnels were given values at the start, so there were no additional values needed to supply to the pour method. In fact, when all the values are filled at the start, the waterwork is actually eagerly executed:
 ```python
from waterworks import Waterwork, add, mul
import pprint

with Waterwork() as ww:
  add_tubes, add_slots = add([1.0, 2.0, 3.0], [3.0, 4.0, 5.0])
  print add_tubes['target'].get_val()
```
```
[4. 6. 8.]
```
However, similar to tensorflow, this system was not really principally designed to run eargerly, but instead to run the same set of computations over and over again with different inputs. So, when defining the waterwork it's not really necessary to supply all values for all the slots at definition. The 'empty' object can be passed to the tank instead, then the values of the funnels can be passed when the actual pour method is run:
```python
from waterworks import Waterwork, add, mul, empty
import pprint

with Waterwork() as ww:
  add_tubes, add_slots = add([1.0, 2.0, 3.0], b=empty)
  div_tubes, div_slots = mul(add_tubes['target'], [2.0, 2.0, 2.0])

taps = ww.pour({'Add_0/slots/b': [3., 4., 5.]}, key_type='str')
pprint.pprint(taps)
taps = ww.pour({'Add_0/slots/b': [5., 6., 7.]}, key_type='str')
pprint.pprint(taps)
```
```
{'Add_0/tubes/a_is_smaller': False,
 'Add_0/tubes/smaller_size_array': array([3., 4., 5.]),
 'Mul_0/tubes/a_is_smaller': False,
 'Mul_0/tubes/missing_vals': array([], dtype=float64),
 'Mul_0/tubes/smaller_size_array': array([2., 2., 2.]),
 'Mul_0/tubes/target': array([ 8., 12., 16.])}
 
 {'Add_0/tubes/a_is_smaller': False,
 'Add_0/tubes/smaller_size_array': array([5., 6., 7.]),
 'Mul_0/tubes/a_is_smaller': False,
 'Mul_0/tubes/missing_vals': array([], dtype=float64),
 'Mul_0/tubes/smaller_size_array': array([2., 2., 2.]),
 'Mul_0/tubes/target': array([12., 16., 20.])}
```
# ML Transforms
