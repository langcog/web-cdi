import numpy

from catsim import irt
from catsim.simulation import Stopper

class CustomStopper(Stopper):
    """Stopping criterion for minimum and maximum number of items in a test, 
    :param min_items: the minimum number of items in the test
    :param max_items: the maximum number of items in the test
    :param min_error: the minimum standard error of estimation the test must achieve before stopping"""

    def __str__(self):
        return 'Min/Max Item Number and Min Error Initializer'

    def __init__(self, min_items: int, max_items: int, min_error: float):
        super(CustomStopper, self).__init__()
        self._max_items = max_items
        self._min_items = min_items
        self._min_error = min_error

    def stop(self, index: int = None, administered_items: numpy.ndarray = None, theta: float = None, **kwargs) -> bool:
        """Checks whether the test reached its stopping criterion for the given user
        :param index: the index of the current examinee
        :param administered_items: a matrix containing the parameters of items that were already administered
        :param min_error: the minimum standard error of estimation the test must achieve before stopping
        :param theta: a float containing the a proficiency value to which the error will be calculated
        :returns: `True` if the test met its stopping criterion, else `False`"""

        if (index is None or self.simulator is None) and administered_items is None:
            raise ValueError

        if administered_items is None and theta is None:
            theta = self.simulator.latest_estimations[index]
            administered_items = self.simulator.items[self.simulator.administered_items[index]]

        if theta is None:
            return False

        n_items = administered_items.shape[0]
        if n_items > self._max_items:
            raise ValueError(
                'More items than permitted were administered: {0} > {1}'.format(
                    n_items, self._max_items
                )
            )
        done = False
        if n_items == self._max_items: # hit the maximum
            done = True
        elif n_items > self._min_items and irt.see(theta, administered_items) < self._min_error:
            done = True # have done minimum and reached min_error
        return done