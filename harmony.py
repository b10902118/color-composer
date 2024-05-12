import numpy as np
from scipy.optimize import minimize_scalar
from scipy.stats import norm


class Template:
    name: str
    sectors: list
    angles: float

    def __init__(self, name: str, sectors: list, angles: float):
        self.name = name
        self.sectors = sectors
        self.angles = angles


# TODO apply class

# Harmonic template types and sector widths (in radians)
TEMPLATE_TYPES = {
    "i": [np.pi * 2 * 0.05],
    "V": [np.pi * 2 * 0.26],
    "L": [np.pi * 2 * 0.05, np.pi * 2 * 0.22],
    "I": [np.pi * 2 * 0.05, np.pi],
    "T": [np.pi],
    "Y": [np.pi * 2 * 0.05, np.pi * 2 * 0.26],
    "X": [np.pi * 2 * 0.26, np.pi],
}


def distance_to_template(hues, template_type, alpha):
    """
    Compute the distance between the hues and the given harmonic template.
    """
    template_sectors = TEMPLATE_TYPES[template_type]
    distances = []
    for h in hues:
        min_dist = np.inf
        for sector in template_sectors:
            sector_start = alpha
            sector_end = alpha + sector
            dist = min(
                abs(h - sector_start),
                abs(h - sector_end),
                min(sector_end - h, h - sector_start),
            )
            min_dist = min(min_dist, dist)
        distances.append(min_dist)
    return np.array(distances)


def harmony_score(hues, saturations, template_type, alpha):
    """
    Compute the harmony score (Eq. 1 in the paper) for the given hues
    and the harmonic template with orientation alpha.
    """
    distances = distance_to_template(hues, template_type, alpha)
    return np.sum(distances * saturations)


def find_best_template(hues, saturations):
    """
    Find the best harmonic template and orientation that minimizes
    the harmony score for the given hues and saturations.
    """
    best_template = None
    best_alpha = None
    min_score = np.inf
    for template_type in TEMPLATE_TYPES:
        res = minimize_scalar(
            lambda alpha: harmony_score(hues, saturations, template_type, alpha)
        )
        score = res.fun
        if score < min_score:
            min_score = score
            best_template = template_type
            best_alpha = res.x
    return best_template, best_alpha


def harmonize_colors(hues, saturations, template_type, alpha, sigma=None):
    """
    Harmonize the colors by shifting the hues to fit the given harmonic template.
    """
    template_sectors = TEMPLATE_TYPES[template_type]
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
