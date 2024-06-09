import numpy as np
from scipy.optimize import minimize_scalar
from scipy.stats import norm

from numpy import pi, radians
from numbers import Number
from tqdm import tqdm
from itertools import product


def rad_distance(h1, h2):  # in radians
    d = abs(h1 - h2)
    return d if d < pi else 2 * pi - d


def ring_distance(h1, h2):
    d = abs(h1 - h2)
    return min(d, 256 - d)


def ring_distance_sign(h1, h2):
    d = ring_distance(h1, h2)
    if h1 + d == h2:
        return d
    return -d


class Sector:
    st: np.int32
    ed: np.int32

    def __init__(self, start, size):
        self.st = np.int32(start % 256)  # %256
        self.ed = np.int32((start + size - 1) % 256)
        self.width = size
        self.center = (self.st + size // 2) % 256
        if self.st < self.ed:
            self._check_range = lambda h: (self.st <= h <= self.ed)
        else:
            self._check_range = lambda h: (h >= self.st or h <= self.ed)

    # def __add__(self, other: Number):
    #    if not isinstance(other, Number):
    #        raise ValueError("Can only add a number to a sector")
    #    return Sector((self.st + other) % 256, (self.ed + other) % 256)

    def __contains__(self, h: Number):
        if h < 0 or h > 255:
            raise ValueError("Hue must be 0-255 int")
        return self._check_range(h)

    def distance(self, h):
        if h in self:
            return 0
        return min(
            ring_distance(h, self.st),
            ring_distance(h, self.ed),
        )


class Template:
    name: str
    sectors: list[Sector]
    alpha: np.int32

    def __init__(
        self,
        name: str,
        sector_sizes: list[float],
        offsets: list[float],
        alpha: float,
    ):
        self.name = name
        self.alpha = alpha
        self.sectors = [
            Sector(alpha + off, size) for off, size in zip(offsets, sector_sizes)
        ]
        self.dists = np.array([self._distance(h) for h in range(256)]).astype(np.int32)

        # debug
        if np.sum(self.dists) <= 0:
            raise ValueError(f"{self.name} {self.alpha} {self.sectors} dists <=0")

    def _distance(self, h):  # may check in first for early return
        min_dist = np.inf
        for sector in self.sectors:
            min_dist = min(min_dist, sector.distance(h))
            if min_dist == 0:
                return 0
        return min_dist


# Harmonic template types and sector widths (in 0-255)
# 26% -> 66.56, 5% -> 12.8, 22% -> 56.32
template_params = [
    ("i", [13], [0]),
    ("V", [67], [0]),
    ("L", [57, 13], [0, 57 + 29]),
    ("I", [13, 13], [0, 128]),
    ("T", [128], [0]),
    ("Y", [67, 13], [0, (256 - 67) // 2 + 67 - 6]),
    ("X", [67, 67], [0, 128]),
]
template_params_dict = {param[0]: param[:] for param in template_params}

# old problem: single color


def harmony_score(hue_weights, template):
    # careful overflow
    # return np.sum(np.vectorize(template.distance)(hues) * saturations / 255) # no faster

    # debug
    if np.any(hue_weights < 0):
        raise ValueError("Weight negative")
    s = np.sum(template.dists * hue_weights)
    # if s == 0:
    #    raise ValueError("sum is zero")
    return s


def minimize_alpha(hue_weights, param):
    min_alpha = None
    min_score = np.inf
    # TODO speed up
    for alpha in range(256):
        score = harmony_score(hue_weights, Template(*param, alpha))
        if score < min_score:
            min_score, min_alpha = score, alpha
    return min_score, min_alpha


def find_best_template(hues, saturations) -> Template:
    hue_weights = np.zeros(256).astype(np.float32)  # don't care precision
    for h, s in zip(hues, saturations / 256):
        hue_weights[h] += s

    best_param = None
    best_alpha = None
    min_score = np.inf
    for param in template_params:
        score, alpha = minimize_alpha(hue_weights, param)
        # TODO wide sector panalty
        # print(param[0], score, alpha)
        if score < min_score:
            min_score, best_param, best_alpha = score, param, alpha

    return Template(*best_param, best_alpha)


def binary_partition(hues, template: Template):
    # primitive
    partition = []
    min_max = 0
    for h in hues:
        min_dist = np.inf
        closest_sector_index = None
        for i, sector in enumerate(template.sectors):
            dist = sector.distance(h)
            if dist < min_dist:
                min_dist = dist
                closest_sector_index = i
        min_max = max(min_max, min_dist)
        partition.append(closest_sector_index)
    # print(min_max)
    return partition


def shift_color(hues, partition, template: Template):
    shifted_hues = []

    new_hues = np.empty((len(template.sectors), 256), dtype=int)
    s_h_combinations = product(range(len(template.sectors)), range(256))
    for s, h in s_h_combinations:
        if s == 2:
            continue
        sector = template.sectors[s]
        C = sector.center  # central hue of the sector
        w = sector.width  # arc-width of the sector
        d = ring_distance_sign(C, h)
        G_sigma = norm.cdf(d / (w / 2))  # Gaussian function
        new_hue = C + (w / 2) * G_sigma
        new_hue = int(new_hue) % 256
        new_hues[s, h] = new_hue

    for h, s in zip(hues, partition):
        # sector = template.sectors[s]
        # C = sector.center  # central hue of the sector
        # w = sector.width  # arc-width of the sector
        # d = ring_distance_sign(C, h)
        # G_sigma = norm.cdf(d / (w / 2))  # Gaussian function
        ## print(d, w, G_sigma)
        # new_hue = C + (w / 2) * (1 - G_sigma)
        # new_hue = int(new_hue) % 256
        shifted_hues.append(new_hues[s, h])
    return np.array(shifted_hues)
