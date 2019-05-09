import transform as n
import pandas as pd
import numpy as np
import warnings
import reversible_transforms.waterworks.placeholder as pl
import reversible_transforms.tanks.tank_defs as td
import reversible_transforms.waterworks.waterwork as wa
import reversible_transforms.waterworks.globs as gl
import reversible_transforms.waterworks.name_space as ns

class NumTransform(n.Transform):
  """Class used to create mappings from raw numerical data to vectorized, normalized data and vice versa.

  Parameters
  ----------
  df : pd.DataFrame
    The dataframe with all the data used to define the mappings.
  columns : list of strs
    The column names of all the relevant columns that make up the data to be taken from the dataframe
  from_file : str
    The path to the saved file to recreate the transform object that was saved to disk.
  save_dict : dict
    The dictionary to rereate the transform object

  Attributes
  ----------
  attribute_list : list of strs
    The list of attributes that need to be saved in order to fully reconstruct the transform object.

  """

  attribute_dict = {'norm_mode': None, 'norm_axis': None, 'fill_nan_func': None, 'name': '', 'mean': None, 'std': None, 'min': None, 'max': None, 'dtype': np.float64, 'input_dtype': None}

  def _setattributes(self, **kwargs):
    super(NumTransform, self)._setattributes(self.attribute_dict, **kwargs)

    if self.norm_mode not in (None, 'min_max', 'mean_std'):
      raise ValueError(self.norm_mode + " not a valid norm mode.")

    if self.fill_nan_func is None:
      self.fill_nan_func = lambda array: np.full(array[np.isnan(array)].shape, np.array(0))

  def calc_global_values(self, array, verbose=True):
    """Set all the attributes which use global information for this subclass that are needed in order to do the final transformation on the individual values of the col_array. e.g. find the mean/std for the mean/std normalization. Null values will be ignored during this step.

    Parameters
    ----------
    array : np.array(
      shape=[num_examples, total_input_dim],
      dtype=self.dtype
    )
      The numpy with all the data needed to define the mappings.
    verbose : bool
      Whether or not to print out warnings, supplementary info, etc.

    """
    # Set the input dtype
    self.input_dtype = array.dtype

    if self.norm_mode == 'mean_std':
      # Find the means and standard deviations of each column
      self.mean = np.nanmean(array, axis=self.norm_axis).astype(self.dtype)
      self.std = np.nanstd(array, axis=self.norm_axis).astype(self.dtype)

      # If any of the standard deviations are 0, replace them with 1's and
      # print out a warning
      if (self.std == 0).any():
        if verbose:
          warnings.warn("NumTransform " + self.name + " has a zero-valued std, replacing with 1.")
        self.std[self.std == 0.] = 1.0

    elif self.norm_mode == 'min_max':
      # Find the means and standard deviations of each column
      self.min = np.nanmin(array, axis=self.norm_axis).astype(self.dtype)
      self.max = np.nanmax(array, axis=self.norm_axis).astype(self.dtype)

      # Test to make sure that min and max are not equal. If they are replace
      # with default values.
      if (self.min == self.max).any():
        self.max[self.max == self.min] = self.max[self.max == self.min] + 1

        if verbose:
          warnings.warn("NumTransform " + self.name + " the same values for min and max, replacing with " + str(self.min) + " " + str(self.max) + " respectively.")

  def define_waterwork(self):
    input = pl.Placeholder(np.ndarray, self.input_dtype, name='input')

    # Replace all the NaT's with the inputted replace_with.
    nans = td.isnan(input)

    replace_with = pl.Placeholder(np.ndarray, self.input_dtype, name='replace_with')
    nums = td.replace(nans['a'], nans['target'], replace_with, name='rp')

    nums['replaced_vals'].set_name('replaced_vals')
    nums['mask'].set_name('nans')

    if self.norm_mode == 'mean_std':
      nums = nums['target'] - self.mean
      nums = nums['target'] / self.std
    elif self.norm_mode == 'min_max':
      nums = nums['target'] - self.min
      nums = nums['target'] / (self.max - self.min)

    nums['target'].set_name('nums')

  def pour(self, array):
    ww = self.get_waterwork()
    tap_dict = ww.pour(
      {'input': array, 'replace_with': self.fill_nan_func(array)},
      key_type='str'
    )
    return {k: tap_dict[k] for k in ['nums', 'nans']}

  def pump(self, nums, nans):
    ww = self.get_waterwork()

    num_nans = len(np.where(nans)[0])
    tap_dict = {
      'nums': nums,
      'nans': nans,
      'replaced_vals': np.full([num_nans], np.nan, dtype=self.input_dtype),
      (self._name('rp'), 'replace_with_shape'): (num_nans,),
    }
    if self.norm_mode == 'mean_std' or self.norm_mode == 'min_max':
      if self.norm_mode == 'mean_std':
        sub_val = self.mean
        div_val = self.std
      else:
        sub_val = self.min
        div_val = self.max - self.min
      norm_mode_dict = {
        ('SubTyped_0/tubes/smaller_size_array'): sub_val,
        ('SubTyped_0/tubes/a_is_smaller'): False,
        ('DivTyped_0/tubes/smaller_size_array'): div_val,
        ('DivTyped_0/tubes/a_is_smaller'): False,
        ('DivTyped_0/tubes/remainder'): np.array([], dtype=self.input_dtype),
        ('DivTyped_0/tubes/missing_vals'): np.array([], dtype=float)
      }
      tap_dict.update(norm_mode_dict)

    ww.pump(tap_dict, key_type='str')
    array = ww.get_placeholder('input').get_val()

    return array
