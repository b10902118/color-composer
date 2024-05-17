import numpy as np
from scipy.optimize import minimize_scalar
from scipy.stats import norm

from numpy import pi, radians
from numbers import Number
from tqdm import tqdm


def rad_distance(h1, h2):  # in radians
    d = abs(h1 - h2)
    return d if d < pi else 2 * pi - d


def ring_distance(h1, h2):
    d = abs(h1 - h2)
    return min(d, 256 - d)


class Sector:
    st: np.int32
    ed: np.int32

    def __init__(self, start, size):
        self.st = np.int32(start % 256)
        self.ed = np.int32((start + size - 1) % 256)
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
    ("Y", [67, 13], [0, 180]),
    ("X", [67, 67], [0, 128]),
]

# old problem: single color


def harmony_score(hue_weights, template):
    # careful overflow
    # return np.sum(np.vectorize(template.distance)(hues) * saturations / 255) # no faster

    # debug
    if np.any(hue_weights < 0):
        raise ValueError("Weight negative")
    s = np.sum(template.dists * hue_weights)
    if s == 0:
        raise ValueError("sum is zero")
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


def harmonize_colors(hues, template_type, alpha, sigma=None):
    template_sectors = T[template_type]
    new_hues = np.zeros_like(hues)
    for i, h in enumerate(hues):
        min_dist = np.inf
        closest_sector = None
        for j, sector in enumerate(template_sectors):
            sector_start = alpha + sum(template_sectors[:j])
            sector_end = sector_start + sector
            dist = min(
                abs(h - sector_start),
                abs(h - sector_end),
                min(sector_end - h, h - sector_start),
            )
            if dist < min_dist:
                min_dist = dist
                closest_sector = j
        sector_width = template_sectors[closest_sector]
        sector_center = (
            alpha + sum(template_sectors[:closest_sector]) + sector_width / 2
        )
        if sigma is None:
            sigma = sector_width / 2
        new_hues[i] = (
            sector_center + (1 - norm.pdf(min_dist, scale=sigma)) * sector_width / 2
        )
    return new_hues
