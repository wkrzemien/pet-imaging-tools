"""Analytic function to compute sensitivity map.
Courtesy of Wojciech Krzemień."""

import numpy as np


def get_cosines(R, L, rho, z):  # pylint: disable=invalid-name
  """
  helper function that returns the pair cosines  which correspond to
  the angles  of the "sensitivy" cones of the detector.
  the are used as a partial results in the various calculations.
  """
  R1 = R - rho  # pylint: disable=invalid-name
  R2 = R + rho  # pylint: disable=invalid-name
  l1 = L / 2. - z
  l2 = L / 2. + z
  denom1 = np.sqrt(l1 * l1 + R1 * R1)
  denom2 = np.sqrt(l1 * l1 + R2 * R2)
  denom3 = np.sqrt(l2 * l2 + R1 * R1)
  denom4 = np.sqrt(l2 * l2 + R2 * R2)
  comp1 = 0
  comp2 = 0

  if z > (rho * L / (2 * R)):
    assert denom1 != 0
    comp1 = l1 / denom1
  else:
    if z <= (rho * L / (2 * R)):
      assert denom4 != 0
      comp1 = l2 / denom4
    else:
      raise AssertionError
  if z > -1. * (rho * L / (2 * R)):
    assert denom2 != 0
    comp2 = l1 / denom2
  else:
    if z <= -1. * (rho * L / (2 * R)):
      assert denom3 != 0
      comp2 = l2 / denom3
    else:
      raise AssertionError
  return comp1, comp2


def fov(R, L, rho, z):  # pylint: disable=invalid-name
  """
  Returns Field-Of-View or geometrical acceptance for gamma pairs (LORS)
  Assumed cylindrical geometry OZ along the cylinder axis.
  The origin point placed inside the centre of the cylinder.
  R - radius,L - length of the cylinder, (rho, z) coordinates of radial and OZ part.
  """
  cosine1, cosine2 = get_cosines(R, L, rho, z)
  return 0.5 * (cosine1 + cosine2)


def fov_factory(R, L, sensitFunction=fov):  # pylint: disable=invalid-name
  """
  Returns a function of signature sensitivity(rho, z)
  where (rho, z) are coordinates of radial and OZ parts.
  The returned function expresses Field-Of-View or geometrical acceptance
  for the cylinder of radius R and length L.
  Assumed cylindrical geometry OZ along the cylinder axis.
  The origin point placed inside the centre of the cylinder.
  Example usage:
  auto sensitivity = fov_factory(50,100) # generation of function for scanner
                                  with and R = 50 and L =100
  sensitivity(5, 10); // geometrical acceptance  for the point  rho = 5 and z = 10
  """

  def _fov(rho, z):
    if rho >= R:
      return 0
    if np.abs(z) >= L / 2.:
      return 0
    return sensitFunction(R, L, rho, z)

  return _fov


def fov_sensitivity(R, L):  # pylint: disable=invalid-name
  sens = fov_factory(R, L)

  def _fov_sensitivity(x, y, z):
    rho = np.sqrt(x * x + y * y)
    return sens(rho, z)

  return _fov_sensitivity
