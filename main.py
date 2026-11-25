"""Set and print the 25 November 2026 issue of The World Ledger."""

from functools import lru_cache
from math import isqrt
from pathlib import Path
from random import Random
import struct
import sys
import zlib


SIZE = 1024
EDGE = 33
RIGHT = SIZE - EDGE
INK = (40, 32, 26)
BODY = (58, 46, 36)
MUTED = (92, 71, 51)
RUST = (125, 53, 37)
RULE = (125, 95, 67)
PAPER = (241, 228, 199)


ISSUE_DATE = 'WEDNESDAY, 25 NOVEMBER 2026'

# Each brief carries its reporting credit in the source edition.
FRONT = (
    ('JIUQUAN / SPACE', ('CHINA TO LAUNCH', 'PAKISTANI INTO', 'ORBIT'),
     ('Shenzhou-24 is due off from Jiuquan.', 'A first orbital flight for Pakistan.'),
     'China Manned Space Agency / Associated Press'),
    ('EUROPE / DIPLOMACY', ('UKRAINE SEEKS', '4-WAY PEACE TALKS'),
     ('Kyiv seeks a seat for Europe', 'alongside the U.S. and Russia.', 'Moscow questions the format.'),
     'AFP / Anadolu Agency'),
    ('FRANCE & U.S. / BUSINESS', ('SANOFI TO BUY', 'INSMED FOR $41B'),
     ('The all-cash deal would add', 'two approved lung medicines.', 'Closing is planned for 2027.'),
     'Sanofi / Insmed'),
)

DESKS = (
    ('North America', (
        ('U.S. confidence rebounds', 'November index near two-year high.', 'Reuters / AP'),
        ('Dell sales more than double', 'AI server demand drives growth.', 'Dell / CNBC'),
        ('King tides flood coastal roads', 'Northern California braces for peaks.', 'AP'),
        ('Nvidia faces calls for hearings', 'U.S. lawmakers question board reversal.', 'CNN / Reuters'),
    )),
    ('Latin America', (
        ('Venezuela tallies $237.5B debt', 'Framework opens path to restructuring.', 'Reuters'),
        ('Brazil Congress clears fiscal bill', 'Lower house backs plan by 352 to 128.', 'The Rio Times'),
        ('Colombia marks decade of accord', 'U.N. urges full delivery of peace terms.', 'UN News'),
        ('Mexico shows arrest footage', 'Video shows detention of cartel figure.', 'BBC'),
    )),
    ('Europe', (
        ('Poland probes drone incursion', 'Authorities investigate airspace breach.', 'The Guardian'),
        ('Hungary leader visits Kyiv', 'First visit opens a new chapter in ties.', 'Kyodo'),
        ('French officer to stand trial', 'Court orders trial over 2023 shooting.', 'France 24'),
        ('Strike hits Zaporizhzhia', 'Officials report two dead and 48 hurt.', 'AP'),
    )),
    ('Africa', (
        ('Congo Ebola teams trapped', 'Fighting blocks responders in Ituri.', 'UN News'),
        ('Nigeria land violence kills dozens', 'Niger state communities report toll.', 'AP / Reuters'),
        ('Libya weighs Benghazi strike', 'Ukraine says it hit a Russian warship.', 'AP'),
        ('Somalia and UAE trade blame', 'Diplomatic tensions rise over security.', 'Inter Press Service'),
    )),
    ('Middle East', (
        ('Israeli strike kills Gaza official', 'Hamas says its security chief died.', 'BBC'),
        ('Syria mine casualties climb', 'Children bear a heavy toll.', 'BBC / Landmine Monitor'),
        ('Yemen braces near Aden', 'Army says Houthi forces are closing in.', 'AP'),
        ('Iraq pushes for power shift', 'Baghdad seeks sway in Kurdistan.', 'The New York Times'),
    )),
    ('South Asia', (
        ('India pledges $1.6B for Nepal', 'Package backs recovery after floods.', 'AP'),
        ('Bangladesh warns exiled leader', 'Officials say return would mean arrest.', 'Dawn'),
        ('Heavy rain forecast in south India', 'Kerala and Tamil Nadu on watch.', 'India Meteorological Department'),
        ('Sri Lanka alerts for heavy rain', 'Forecast flags local falls above 75 mm.', 'Sri Lanka Disaster Management Centre'),
    )),
    ('East Asia', (
        ('Seoul subway strike averted', 'Wage deal keeps trains running.', 'Yonhap / SBS'),
        ('China probes Shanghai official', 'Party watchdog opens disciplinary case.', 'AP / Xinhua'),
        ('Japan backs sanctions-hit court', 'Tokyo pledges early 2027 ICC payment.', 'AP'),
        ('Huawei gets split U.S. verdict', 'Guilty of theft, cleared of racketeering.', 'BBC'),
    )),
    ('Southeast Asia', (
        ('Hanoi restaurant blast kills six', 'More than a dozen reported injured.', 'The Star'),
        ('Philippine court rejects petitions', 'Judges deny bids to free ex-president.', 'The Star'),
        ('Thailand projects skills shortfall', 'Needs 1.1M skilled workers by 2029.', 'The Star'),
        ('Singapore raises growth forecast', 'Third-quarter GDP up 6.1% on year.', 'METI / CNA'),
    )),
    ('Oceania', (
        ('Cook Islands plans ocean dives', 'China joins local deep-sea team.', 'RNZ Pacific'),
        ('New Zealand TV staff cancel strike', 'TVNZ workers call off 24-hour action.', '1News / RNZ'),
        ('Canberra defends U.S. alliance', 'Minister urges keeping close ties.', 'AAP / PACNEWS'),
        ('Pacific elders fault climate talks', 'Group says summit widened trust gap.', 'PACNEWS'),
    )),
)


# The dots are open paper. Each group gives the face from top to bottom.
FORMS = {
    'A': '.###./##.##/##.##/#####/##.##/##.##/##.##',
    'B': '####./##.##/##.##/####./##.##/##.##/####.',
    'C': '.####/##..#/##.../##.../##.../##..#/.####',
    'D': '####./##.##/##.##/##.##/##.##/##.##/####.',
    'E': '#####/##.../##.../####./##.../##.../#####',
    'F': '#####/##.../##.../####./##.../##.../##...',
    'G': '.####/##.../##.../##.##/##.##/##.##/.####',
    'H': '##.##/##.##/##.##/#####/##.##/##.##/##.##',
    'I': '###/.#./.#./.#./.#./.#./###',
    'J': '..###/...##/...##/...##/...##/#..##/.###.',
    'K': '##.##/##.##/####./###../####./##.##/##.##',
    'L': '##.../##.../##.../##.../##.../##..#/#####',
    'M': '##..##/######/######/##..##/##..##/##..##/##..##',
    'N': '##.##/##.##/#####/#####/#####/##.##/##.##',
    'O': '.###./##.##/##.##/##.##/##.##/##.##/.###.',
    'P': '####./##.##/##.##/####./##.../##.../##...',
    'Q': '.###./##.##/##.##/##.##/##.##/##.##/.###./...##',
    'R': '####./##.##/##.##/####./###../##.##/##.##',
    'S': '.####/##.../##.../.###./...##/...##/####.',
    'T': '#####/#.#.#/..#../..#../..#../..#../.###.',
    'U': '##.##/##.##/##.##/##.##/##.##/##.##/.###.',
    'V': '##.##/##.##/##.##/##.##/##.##/.###./..#..',
    'W': '##...##/##...##/##...##/##.#.##/#######/###.###/##...##',
    'X': '##.##/##.##/.###./..#../.###./##.##/##.##',
    'Y': '##.##/##.##/.###./..#../..#../..#../.###.',
    'Z': '#####/...##/..##./.##../##.../##.../#####',
    'a': '...../...../.###./....#/.####/#...#/.####',
    'b': '#..../#..../####./#...#/#...#/#...#/####.',
    'c': '...../...../.###./#...#/#..../#...#/.###.',
    'd': '....#/....#/.####/#...#/#...#/#...#/.####',
    'e': '...../...../.###./#...#/#####/#..../.####',
    'f': '..##./.#..#/###../.#.../.#.../.#.../.#...',
    'g': '...../...../.####/#...#/#...#/.####/....#/.###.',
    'h': '#..../#..../####./#...#/#...#/#...#/#...#',
    'i': '#/./#/#/#/#/#',
    'j': '..#/.../..#/..#/..#/..#/..#/##.',
    'k': '#..../#..../#..#./#.#../##.../#.#../#..#.',
    'l': '#/#/#/#/#/#/#',
    'm': '......./......./###.##./#..#..#/#..#..#/#..#..#/#..#..#',
    'n': '...../...../####./#...#/#...#/#...#/#...#',
    'o': '...../...../.###./#...#/#...#/#...#/.###.',
    'p': '...../...../####./#...#/#...#/#...#/####./#..../#....',
    'q': '...../...../.####/#...#/#...#/#...#/.####/....#/....#',
    'r': '..../..../#.##/##../#.../#.../#...',
    's': '...../...../.####/#..../.###./....#/####.',
    't': '.../.#./###/.#./.#./.#./..#',
    'u': '...../...../#...#/#...#/#...#/#...#/.####',
    'v': '...../...../#...#/#...#/#...#/.#.#./..#..',
    'w': '......./......./#.....#/#.....#/#..#..#/#..#..#/.##.##.',
    'x': '...../...../#...#/.#.#./..#../.#.#./#...#',
    'y': '...../...../#...#/#...#/#...#/.####/....#/....#/.###.',
    'z': '...../...../#####/...#./..#../.#.../#####',
    '0': '.###./#...#/#...#/#...#/#...#/#...#/.###.',
    '1': '.#./##./.#./.#./.#./.#./###',
    '2': '.###./#...#/....#/...#./..#../.#.../#####',
    '3': '####./....#/....#/.###./....#/....#/####.',
    '4': '...#./..##./.#.#./#..#./#####/...#./...#.',
    '5': '#####/#..../#..../####./....#/....#/####.',
    '6': '.####/#..../#..../####./#...#/#...#/.###.',
    '7': '#####/....#/...#./..#../.#.../.#.../.#...',
    '8': '.###./#...#/#...#/.###./#...#/#...#/.###.',
    '9': '.###./#...#/#...#/.####/....#/....#/####.',
    '.': '././././././#',
    ',': '../../../../../.#/.#/#.',
    "'": '##/.#/#./../../../../..',
    '-': '.../.../.../###/.../.../...',
    '&': '.##../#..#./#.#../.#.../#.#.#/#..#./.##.#',
    '$': '..#../.####/#.#../.###./..#.#/####./..#..',
    '%': '##.../##..#/...#./..#../.#.../#..##/...##',
    '/': '..#/..#/.#./.#./.#./#../#..',
    '?': '.###./#...#/....#/...#./..#../...../..#..',
    ' ': '.../.../.../.../.../.../...',
}


GRIDS = {
    letter: tuple(tuple(mark == '#' for mark in row.strip()) for row in form.split('/'))
    for letter, form in FORMS.items()
}


DISPLAY_FORMS = {
    'A': '..#../.#.#./#...#/#...#/#####/#...#/#...#',
    'C': '.###./#...#/#..../#..../#..../#...#/.###.',
    'G': '.###./#...#/#..../#.###/#...#/#...#/.###.',
    'M': '#....#/##..##/#.##.#/#.##.#/#....#/#....#/#....#',
    'N': '#...#/##..#/##..#/#.#.#/#..##/#..##/#...#',
    'S': '.###./#...#/#..../.###./....#/#...#/.###.',
    'T': '#####/..#../..#../..#../..#../..#../..#..',
    'U': '#...#/#...#/#...#/#...#/#...#/##.##/.###.',
    'W': '#.....#/#.....#/#.....#/#..#..#/#.#.#.#/##...##/#.....#',
}
DISPLAY_GRIDS = {
    letter: tuple(tuple(mark == '#' for mark in row) for row in form.split('/'))
    for letter, form in DISPLAY_FORMS.items()
}


def advances(text, height, width_scale):
    steps = []
    for letter in text:
        grid = GRIDS.get(letter, GRIDS['?'])
        width = max(1, round(len(grid[0]) * height * width_scale / 7))
        gap = max(1, round(height * 0.14))
        steps.append((letter, width, gap))
    return steps


def measure(text, height, width_scale=0.8):
    steps = advances(text, height, width_scale)
    return sum(width + gap for _, width, gap in steps) - (steps[-1][2] if steps else 0)


def smooth_sample(grid, x, y):
    x = min(len(grid[0]) - 1.0, max(0.0, x))
    y = min(len(grid) - 1.0, max(0.0, y))
    col, row = int(x), int(y)
    dx, dy = x - col, y - row
    next_col = min(col + 1, len(grid[0]) - 1)
    next_row = min(row + 1, len(grid) - 1)
    top = grid[row][col] * (1 - dx) + grid[row][next_col] * dx
    bottom = grid[next_row][col] * (1 - dx) + grid[next_row][next_col] * dx
    return top * (1 - dy) + bottom * dy


@lru_cache(maxsize=512)
def impression(letter, height, width, strong, display):
    grid = GRIDS.get(letter, GRIDS['?'])
    if display:
        grid = DISPLAY_GRIDS.get(letter, grid)
    rows = round(len(grid) * height / 7)
    dots = []
    threshold = 0.36 if strong else 0.46
    for y in range(rows):
        for x in range(width):
            coverage = 0
            for sy in (0.2, 0.7):
                for sx in (0.2, 0.7):
                    gx = (x + sx) * len(grid[0]) / width - 0.5
                    gy = (y + sy) * len(grid) / rows - 0.5
                    coverage += smooth_sample(grid, gx, gy) >= threshold
            if coverage:
                dots.append((x, y, coverage))
    return dots


@lru_cache(maxsize=512)
def ink_fringe(letter, height, width, strong, display):
    """Find open pixels just below or to the right of a solid stroke."""
    dots = impression(letter, height, width, strong, display)
    occupied = {(x, y) for x, y, _ in dots}
    fringe = set()
    for x, y, coverage in dots:
        if coverage == 4:
            fringe.update(((x + 1, y), (x, y + 1)))
    return tuple(sorted(fringe - occupied))


def print_type(page, x, y, text, height, color, *, strong=False, limit=None,
               width_scale=0.8, display=False):
    if limit is not None:
        while measure(text, height, width_scale) > limit and height > 10:
            height -= 1
    for index, (letter, width, gap) in enumerate(advances(text, height, width_scale)):
        unevenness = ((x * 29) ^ (y * 43) ^ (index * 97) ^ (ord(letter) * 61))
        pressure = unevenness % 31
        rise = int(height >= 38 and (ord(letter) + index) % 7 == 0)
        top = y + rise
        if height >= 17:
            spread, spread_range = (24, 22) if height >= 30 else (11, 10)
            spread += pressure * spread_range // 30
            for dx, dy in ink_fringe(letter, height, width, strong, display):
                page.ink(x + dx, top + dy, color, spread)

        # Small type keeps nearly full pressure even on the lightest sort.
        variation = 30 if height >= 30 else 20
        strength = 255 - (30 - pressure) * variation // 30
        for dx, dy, coverage in impression(letter, height, width, strong, display):
            opacity = strength
            if height >= 30:
                streak = ((dy // 3 * 11) ^ (dx // 5 * 7) ^ pressure) % 13
                fleck = ((dx * 37) ^ (dy * 71) ^ (x * 29) ^ (top * 23)) % 113
                opacity -= streak + (34 if fleck == 0 else 0)
            page.ink(x + dx, top + dy, color, coverage * opacity // 4)
        x += width + gap
    return x


class Page:
    def __init__(self):
        self.pixels = bytearray(bytes(PAPER) * SIZE * SIZE)

    def box(self, x, y, width, height, color):
        left, right = max(0, x), min(SIZE, x + width)
        top, bottom = max(0, y), min(SIZE, y + height)
        if left >= right or top >= bottom:
            return
        stripe = bytes(color) * (right - left)
        for row in range(top, bottom):
            start = 3 * (row * SIZE + left)
            self.pixels[start:start + len(stripe)] = stripe

    def ink(self, x, y, color, opacity):
        if not (0 <= x < SIZE and 0 <= y < SIZE):
            return
        index = 3 * (y * SIZE + x)
        for channel, value in enumerate(color):
            old = self.pixels[index + channel]
            self.pixels[index + channel] = (old * (255 - opacity) + value * opacity) // 255

    def line(self, x1, y1, x2, y2, color, width=1):
        dx, dy = abs(x2 - x1), -abs(y2 - y1)
        step_x = 1 if x1 < x2 else -1
        step_y = 1 if y1 < y2 else -1
        error = dx + dy
        while True:
            self.box(x1, y1, width, width, color)
            if x1 == x2 and y1 == y2:
                break
            change = 2 * error
            if change >= dy:
                error += dy
                x1 += step_x
            if change <= dx:
                error += dx
                y1 += step_y

    def ellipse(self, x, y, rx, ry, color):
        for row in range(-ry, ry + 1):
            half = isqrt(rx * rx * (ry * ry - row * row)) // ry
            self.box(x - half, y + row, half * 2 + 1, 1, color)

    def polygon(self, points, color):
        edges = tuple(zip(points, points[1:] + points[:1]))
        for y in range(min(y for _, y in points), max(y for _, y in points) + 1):
            changes = []
            for (x1, y1), (x2, y2) in edges:
                if min(y1, y2) <= y < max(y1, y2):
                    changes.append(x1 + (y - y1) * (x2 - x1) // (y2 - y1))
            changes.sort()
            for left, right in zip(changes[::2], changes[1::2]):
                self.box(left, y, right - left + 1, 1, color)

    def png(self):
        stride = 3 * SIZE
        scanlines = bytearray()
        for offset in range(0, len(self.pixels), stride):
            row = self.pixels[offset:offset + stride]
            scanlines.append(1)
            scanlines.extend(row[:3])
            scanlines.extend(
                (channel - row[index]) & 255
                for index, channel in enumerate(row[3:])
            )

        def chunk(tag, data):
            return (
                struct.pack('>I', len(data)) + tag + data
                + struct.pack('>I', zlib.crc32(tag + data))
            )

        return b'\x89PNG\r\n\x1a\n' + b''.join((
            chunk(b'IHDR', struct.pack('>IIBBBBB', SIZE, SIZE, 8, 2, 0, 0, 0)),
            chunk(b'IDAT', zlib.compress(scanlines, 9)),
            chunk(b'IEND', b''),
        ))


def paper_mottle(rng, spacing, amplitude):
    """Interpolate seeded tone samples at one spatial scale."""
    count = (SIZE - 1) // spacing + 2
    grid = [[rng.randint(-amplitude, amplitude) for _ in range(count)]
            for _ in range(count)]
    positions = [divmod(x, spacing) for x in range(SIZE)]
    area = spacing * spacing
    for row, dy in positions:
        upper, lower = grid[row], grid[row + 1]
        blended = [a * (spacing - dy) + b * dy for a, b in zip(upper, lower)]
        yield [(blended[col] * (spacing - dx) + blended[col + 1] * dx + area // 2) // area
               for col, dx in positions]


def aged_paper(page):
    rng = Random(20261124)
    broad = paper_mottle(rng, 126, 6)
    fine = paper_mottle(rng, 19, 3)
    red, green, blue = PAPER
    for y, (broad_row, fine_row) in enumerate(zip(broad, fine)):
        stripe = bytearray()
        for x, (broad_tone, fine_tone) in enumerate(zip(broad_row, fine_row)):
            edge = min(x, SIZE - 1 - x, y, SIZE - 1 - y)
            corner = (x + 30) ** 2 + (y - 1004) ** 2
            cloud = (x - 922) ** 2 + (y + 75) ** 2
            age = max(0, (420 ** 2 - corner) * 13 // 420 ** 2)
            age += max(0, (375 ** 2 - cloud) * 10 // 375 ** 2)
            age += max(0, 29 - edge) ** 2 // 57
            shade = age + broad_tone + fine_tone
            stripe.extend((red - shade, green - shade - age // 3,
                           blue - shade - age // 2))
        start = 3 * y * SIZE
        page.pixels[start:start + len(stripe)] = stripe

    for _ in range(25000):
        x = rng.randrange(SIZE)
        y = rng.randrange(SIZE)
        grain = rng.choice(((195, 170, 132), (216, 194, 151), (255, 248, 226)))
        page.ink(x, y, grain, rng.randint(13, 50))
    for _ in range(3200):
        x = rng.randrange(SIZE)
        y = rng.randrange(SIZE)
        fiber = rng.choice(((186, 157, 119), (254, 247, 223)))
        opacity = rng.randint(23, 54)
        slope = rng.choice((-1, 0, 0, 1))
        page.ink(x, y, fiber, opacity)
        page.ink(x + 1, y + slope, fiber, opacity * 2 // 3)
        if opacity >= 44:
            page.ink(x + 2, y + slope, fiber, opacity // 3)
    for x, y in ((4, 366), (1013, 217), (13, 938), (996, 1018), (181, 4)):
        for _ in range(54):
            dx = rng.randrange(-15, 16)
            dy = rng.randrange(-9, 10)
            if 3 * abs(dx) + 5 * abs(dy) < 61:
                page.ink(x + dx, y + dy, RULE, rng.randrange(22, 100))
    for x, y in ((5, 24), (13, 1019), (1007, 1005)):
        page.line(x, y, x + 12, y - 7, (224, 202, 167))
        page.line(x + 2, y + 1, x + 12, y - 4, (232, 216, 185))


def press_rule(page, start, end, y, color=RULE, weight=1):
    x = start
    while x < end:
        span = min(26 + (x * 11 + y) % 30, end - x)
        shift = int((x + y * 3) % 11 == 0)
        page.box(x, y + shift, span, weight, color)
        x += span + int((x ^ y) % 7 == 0)


def centered(page, text, y, size, color, strong=False, width_scale=0.8):
    width = measure(text, size, width_scale)
    print_type(page, (SIZE - width) // 2, y, text, size, color,
               strong=strong, width_scale=width_scale)


def masthead(page):
    press_rule(page, EDGE, RIGHT, 20, INK, 2)
    print_type(page, EDGE, 28, ISSUE_DATE.upper(), 14, INK, strong=True)
    edition = 'WORLD EDITION'
    edition_x = RIGHT - measure(edition, 14)
    print_type(page, edition_x, 28, edition, 14, RUST, strong=True)
    press_rule(page, EDGE, RIGHT, 48)
    centered(page, 'THE WORLD LEDGER', 57, 62, INK, strong=True, width_scale=0.88)
    press_rule(page, EDGE, RIGHT, 126, INK, 3)
    press_rule(page, EDGE, RIGHT, 132)


def engraved_panel(page, left, top, width, height, ground, grain, seed):
    page.box(left, top, width, height, ground)
    rng = Random(seed)
    for _ in range(width * height // 4):
        x, y = rng.randrange(width), rng.randrange(height)
        page.ink(left + x, top + y, grain, rng.randrange(24, 100))
    press_rule(page, left, left + width, top + height - 1, grain)


def launch_engraving(page, left, top, width):
    night = (45, 62, 66)
    blue = (95, 123, 126)
    gilt = (215, 176, 112)
    ivory = (236, 220, 177)
    engraved_panel(page, left, top, width, 89, night, blue, 2524)
    cx = left + width // 2
    rng = Random(241125)
    for _ in range(104):
        x, y = rng.randrange(left + 5, left + width - 5), rng.randrange(top + 4, top + 65)
        page.ink(x, y, ivory, rng.randrange(95, 195))
    for shift in (0, 5, 10):
        page.line(left + 7, top + 66 + shift, cx - 25, top + 33 + shift, blue)
        page.line(cx + 25, top + 35 + shift, left + width - 8, top + 8 + shift, blue)
    horizon = [(left, top + 85), (left + 58, top + 64), (left + 107, top + 71),
               (cx, top + 65), (left + width - 75, top + 63),
               (left + width, top + 77), (left + width, top + 89), (left, top + 89)]
    page.polygon(horizon, (102, 107, 91))
    page.polygon([(cx - 12, top + 55), (cx + 12, top + 55),
                  (cx + 31, top + 87), (cx - 31, top + 87)], (173, 116, 71))
    for y in range(57, 87, 4):
        page.line(cx - 10 - (y - 57) // 2, top + y,
                  cx + 13 + (y - 57) // 3, top + y + 1, gilt)
    page.polygon([(cx, top + 5), (cx + 7, top + 17), (cx + 9, top + 46),
                  (cx + 17, top + 57), (cx - 17, top + 57),
                  (cx - 9, top + 46), (cx - 7, top + 17)], ivory)
    page.line(cx + 5, top + 20, cx + 6, top + 53, gilt, 2)
    page.box(cx - 7, top + 29, 14, 3, (151, 61, 46))
    page.line(cx - 22, top + 48, cx - 22, top + 75, ivory)
    page.line(cx - 22, top + 53, cx - 12, top + 53, ivory)
    page.ellipse(left + width - 55, top + 26, 12, 12, gilt)
    page.ellipse(left + width - 51, top + 23, 10, 10, night)


def talks_engraving(page, left, top, width):
    green = (77, 102, 91)
    shade = (47, 68, 64)
    light = (225, 213, 169)
    engraved_panel(page, left, top, width, 89, green, shade, 2525)
    cx = left + width // 2
    for x in range(left + 9, left + width - 9, 11):
        page.line(x, top + 71, cx + (x - cx) // 2, top + 14, shade)
    for x in (cx - 64, cx - 22, cx + 23, cx + 66):
        page.ellipse(x, top + 26, 7, 8, light)
        page.ellipse(x, top + 44, 14, 11, light)
    page.polygon([(cx - 87, top + 42), (cx + 85, top + 42),
                  (cx + 111, top + 70), (cx - 111, top + 70)], (193, 170, 119))
    page.box(cx - 111, top + 70, 222, 7, shade)
    for x in (cx - 64, cx - 22, cx + 23, cx + 66):
        page.line(x - 8, top + 58, x + 8, top + 58, light, 3)
        page.line(x + 10, top + 67, x + 6, top + 46, shade, 2)
        page.box(x + 2, top + 45, 8, 3, shade)
    press_rule(page, cx - 96, cx + 98, top + 72, light)


def pharma_engraving(page, left, top, width):
    clay = (156, 90, 69)
    wine = (111, 53, 47)
    ivory = (237, 219, 178)
    engraved_panel(page, left, top, width, 89, clay, wine, 2526)
    cx = left + width // 2
    for y in range(top + 11, top + 82, 6):
        press_rule(page, left + 6, left + width - 6, y, wine)
    for x, lift in ((cx - 51, 5), (cx - 4, 0), (cx + 43, 11)):
        y = top + 18 + lift
        page.box(x - 14, y + 12, 30, 45 - lift, wine)
        page.ellipse(x, y + 15, 14, 10, ivory)
        page.box(x - 13, y + 15, 27, 38 - lift, ivory)
        page.box(x - 10, y, 21, 10, (176, 157, 127))
        for offset in range(-8, 10, 4):
            page.box(x + offset, y + 1, 1, 8, wine)
        page.box(x - 11, top + 49, 23, 12, (194, 156, 120))
        page.line(x - 7, top + 54, x + 8, top + 54, wine)
    press_rule(page, left + 4, left + width - 4, top + 75, ivory)


def front_story(page):
    columns = (
        (EDGE, 340, 31, (250, 283, 316), (351, 370), launch_engraving),
        (397, 290, 26, (253, 283), (324, 344, 364), talks_engraving),
        (710, 281, 26, (253, 283), (324, 344, 364), pharma_engraving),
    )
    for x in (384, 698):
        page.line(x, 140, x + 1, 380, RULE)
    for column, story in zip(columns, FRONT):
        left, width, height, headline_rows, deck_rows, illustration = column
        label, headline, deck, _ = story
        print_type(page, left + 1, 140, label, 14, RUST, strong=True)
        illustration(page, left, 157, width)
        for y, row in zip(headline_rows, headline):
            print_type(page, left, y, row, height, INK, strong=True, limit=width, display=True)
        for y, row in zip(deck_rows, deck):
            print_type(page, left + 1, y, row, 15, BODY, limit=width - 2)
    press_rule(page, EDGE, RIGHT, 388, INK, 3)
    press_rule(page, EDGE, RIGHT, 393)


def world_pages(page):
    column_width = 302
    column_pitch = 326
    row_pitch = 195
    grid_top = 402
    for index, (region, articles) in enumerate(DESKS):
        column, row = index % 3, index // 3
        left = EDGE + column * column_pitch
        top = grid_top + row * row_pitch
        print_type(page, left, top + 2, region.upper(), 17, RUST,
                   strong=True, limit=column_width)
        press_rule(page, left, left + column_width, top + 23)
        for article, (headline, deck, _) in enumerate(articles):
            y = top + 31 + article * 39
            print_type(page, left, y, headline, 16, INK,
                       strong=True, limit=column_width)
            print_type(page, left, y + 21, deck, 12, BODY, limit=column_width)
            if article < len(articles) - 1:
                press_rule(page, left, left + column_width, y + 37, (165, 136, 106))
        if row < 2:
            press_rule(page, left, left + column_width, top + 185, RULE, 2)
    for x in (347, 673):
        page.line(x, grid_top, x + 1, 985, RULE)


def make_page():
    page = Page()
    aged_paper(page)
    masthead(page)
    front_story(page)
    world_pages(page)
    press_rule(page, EDGE, RIGHT, 987, INK, 2)
    press_rule(page, EDGE, RIGHT, 994, RULE)
    return page


if __name__ == '__main__':
    output = Path(sys.argv[1] if len(sys.argv) > 1 else '/output/entry.png')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(make_page().png())
