import numpy as np


from .abc import Codec
from .compat import ensure_ndarray, ndarray_copy


class SpatialDelta(Codec):
    """Codec to encode data as the difference between adjacent values.

    Parameters
    ----------
    axis : number
        Axis to compute delta
    dtype : dtype
        Data type to use for decoded data.
    astype : dtype, optional
        Data type to use for encoded data.

    Notes
    -----
    If `astype` is an integer data type, please ensure that it is
    sufficiently large to store encoded values. No checks are made and data
    may become corrupted due to integer overflow if `astype` is too small.
    Note also that the encoded data for each chunk includes the absolute
    value of the first element in the chunk, and so the encoded data type in
    general needs to be large enough to store absolute values from the array.

    Examples
    --------
    >>> import numcodecs
    >>> import numpy as np
    >>> x = np.arange(27, dtype = 'i2').reshape(3,3,3)
    >>> codec = numcodecs.SpatialDelta(axis = 1,dtype='i2', astype='i1')
    >>> y = codec.encode(x)
    >>> y
    array([[[ 0,  1,  2],
            [ 3,  3,  3],
            [ 3,  3,  3]],

           [[ 9, 10, 11],
            [ 3,  3,  3],
            [ 3,  3,  3]],

           [[18, 19, 20],
            [ 3,  3,  3],
            [ 3,  3,  3]]], dtype=int8)
    >>> z = codec.decode(y)
    >>> z
    array([[[ 0,  1,  2],
            [ 3,  4,  5],
            [ 6,  7,  8]],

           [[ 9, 10, 11],
            [12, 13, 14],
            [15, 16, 17]],

           [[18, 19, 20],
            [21, 22, 23],
            [24, 25, 26]]], dtype=int16)
    """

    codec_id = 'spatial_delta'

    def __init__(self, axis, dtype, astype=None):
        self.axis = axis
        self.dtype = np.dtype(dtype)
        if astype is None:
            self.astype = self.dtype
        else:
            self.astype = np.dtype(astype)
        if self.dtype == np.dtype(object) or self.astype == np.dtype(object):
            raise ValueError('object arrays are not supported')

    def encode(self, buf):
        # normalise input
        arr = ensure_ndarray(buf).view(self.dtype)

        # flatten to simplify implementation
        # arr = arr.reshape(-1, order='A')

        # setup encoded output
        enc = np.empty_like(arr, dtype = self.astype)

        # set first element
        slice_idx = [slice(0, None) for _ in range(arr.ndim)]
        slice_idx[self.axis] = slice(0,1)
        enc[*slice_idx] = arr[*slice_idx]

        # compute differences
        slice_idx[self.axis] = slice(1, None)
        enc[*slice_idx] = np.diff(arr, axis = self.axis)

        return enc

    def decode(self, buf, out=None):
        # normalise input
        enc = ensure_ndarray(buf).view(self.astype)

        # flatten to simplify implementation

        # setup decoded output
        dec = np.empty_like(enc, dtype=self.dtype)

        # decode differences
        np.cumsum(enc, axis = self.axis, out=dec)

        # handle output
        out = ndarray_copy(dec, out)

        return out

    def get_config(self):
        # override to handle encoding dtypes
        return dict(id=self.codec_id, dtype=self.dtype.str, astype=self.astype.str)

    def __repr__(self):
        r = f'{type(self).__name__}(dtype={self.dtype.str!r}, axis={self.axis}'
        if self.astype != self.dtype:
            r += f', astype={self.astype.str!r}'
        r += ')'
        return r
