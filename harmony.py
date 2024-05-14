import numpy as np
from scipy.optimize import minimize_scalar
from scipy.stats import norm

from numpy import pi, radians
from numbers import Number


def rad_distance(h1, h2):  # in radians
    d = abs(h1 - h2)
    return d if d < pi else 2 * pi - d


class Sector:
    st: float
    ed: float

    def __init__(self, start: float, end: float):
        self.st = start
        self.ed = end

    def __add__(self, other: Number):
        if not isinstance(other, Number):
            raise ValueError("Can only add a number to a sector")
        return Sector(self.st + other, self.ed + other)

    def __contains__(self, h: Number):
        if h < 0 or h >= 2 * pi:
            raise ValueError("Hue must be converted by radians() to be in [0, 2*pi)")
        if self.st < self.ed:
            return self.st <= h <= self.ed
        else:  # If the range crosses the 2*pi boundary
            return h >= self.ed or h <= self.st

    def distance(self, h):
        if h in self:
            return 0
        return min(
            rad_distance(h, self.st),
            rad_distance(h, self.ed),
        )


class Template:
    name: str
    sectors: list[Sector]

    def __init__(
        self,
        name: str,
        sector_sizes: list[float],
        center_angles: list[float],
        alpha: float,
    ):
        self.name = name
        center_radians = [radians(angle + alpha) for angle in center_angles]
        self.sectors = [
            Sector(radians(rad - size) / 2, radians(rad + size / 2))
            for rad, size in zip(center_radians, sector_sizes)
        ]

    def distance(self, h):  # may check in first for early return
        min_dist = np.inf
        for sector in self.sectors:
            min_dist = min(min_dist, sector.distance(h))
            if min_dist == 0:
                return 0
        return min_dist


# Harmonic template types and sector widths (in radians)
template_params = [
    ("i", [pi * 2 * 0.05], [0]),
    ("V", [pi * 2 * 0.26], [0]),
    ("L", [pi * 2 * 0.22, pi * 2 * 0.05], [0, 90]),
    ("I", [pi * 2 * 0.05, pi * 2 * 0.05], [0, 180]),
    ("T", [pi], [0]),
    ("Y", [pi * 2 * 0.26, pi * 2 * 0.05], [0, 180]),
    ("X", [pi * 2 * 0.26, pi * 2 * 0.26], [0, 180]),
]

# old problem: single color


def harmony_score(hues, saturations, param, alpha):
    template = Template(*param, alpha)
    return np.sum(template.distance(h) * s for h, s in zip(hues, saturations))


def find_best_template(hues, saturations):
    best_param = None
    min_score = np.inf
    for param in template_params:
        res = minimize_scalar(
            lambda alpha: harmony_score(hues, saturations, param, alpha)
        )
        score = res.fun
        if score < min_score:
            min_score = score
            best_param = (*param, res.x)
    return best_param


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
