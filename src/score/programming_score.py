import re


def score_cpu(cpu):
    if not cpu or cpu == "Unknown":
        return 0

    cpu_lower = cpu.lower()

    # --------------------------------------------------
    # Intel Core Ultra
    # --------------------------------------------------
    if "core ultra 9" in cpu_lower:
        return 55

    if "core ultra 7" in cpu_lower:
        return 52

    if "core ultra 5" in cpu_lower:
        return 47

    # --------------------------------------------------
    # New Intel Core naming
    # Examples:
    # Intel Core 7 Processor 150U
    # Intel Core 5 120U
    # Intel Core 3 100U
    # --------------------------------------------------
    if re.search(r"\bcore[™\s]+7\b", cpu_lower):
        return 46

    if re.search(r"\bcore[™\s]+5\b", cpu_lower):
        return 42

    if re.search(r"\bcore[™\s]+3\b", cpu_lower):
        return 34

    # --------------------------------------------------
    # AMD Ryzen 9 / 7 / 5
    # --------------------------------------------------
    if "ryzen 9" in cpu_lower:
        return 55

    if "ryzen 7" in cpu_lower:
        return 50

    if "ryzen 5" in cpu_lower:
        return 44

    # --------------------------------------------------
    # Intel Core i9
    # --------------------------------------------------
    match = re.search(r"\bi9[-\s]?(\d{4,5})", cpu_lower)

    if match:
        model = match.group(1)
        generation = _intel_generation(model)

        if generation >= 12:
            return 53
        elif generation >= 10:
            return 48
        elif generation >= 8:
            return 42
        else:
            return 32

    # Generic i9 fallback
    if "core i9" in cpu_lower or "intel i9" in cpu_lower:
        return 45

    # --------------------------------------------------
    # Intel Core i7
    # --------------------------------------------------
    match = re.search(r"\bi7[-\s]?(\d{4,5})", cpu_lower)

    if match:
        model = match.group(1)
        generation = _intel_generation(model)

        if generation >= 12:
            return 50
        elif generation >= 10:
            return 44
        elif generation >= 8:
            return 36
        else:
            return 25

    # --------------------------------------------------
    # Intel Core i5
    # --------------------------------------------------

    # Amazon sometimes reports shortened 13th-gen models.
    # Example: Intel i5-1342H
    if re.search(r"\bi5[-\s]?13\d{2}[a-z]*\b", cpu_lower):
        return 44

    match = re.search(r"\bi5[-\s]?(\d{4,5})", cpu_lower)

    if match:
        model = match.group(1)
        generation = _intel_generation(model)

        if generation >= 12:
            return 46
        elif generation >= 10:
            return 40
        elif generation >= 8:
            return 32
        else:
            return 22

    # --------------------------------------------------
    # Intel Core i3
    # --------------------------------------------------
    match = re.search(r"\bi3[-\s]?(\d{4,5})", cpu_lower)

    if match:
        model = match.group(1)
        generation = _intel_generation(model)

        if generation >= 12:
            return 35
        elif generation >= 10:
            return 30
        elif generation >= 8:
            return 25
        else:
            return 18

    # --------------------------------------------------
    # Generic Intel Core fallbacks
    # --------------------------------------------------
    if "core i7" in cpu_lower or "intel i7" in cpu_lower:
        return 32

    if "core i5" in cpu_lower or "intel i5" in cpu_lower:
        return 28

    if "core i3" in cpu_lower or "intel i3" in cpu_lower:
        return 22

    # --------------------------------------------------
    # Entry-level processors
    # --------------------------------------------------
    if "celeron" in cpu_lower:
        return 10

    if "pentium" in cpu_lower:
        return 12

    if re.search(r"\bamd\s+a\d+", cpu_lower):
        return 8

    if "core m3" in cpu_lower or re.search(r"\bm3-", cpu_lower):
        return 12

    # Unknown-but-recognized CPU format
    return 15


def _intel_generation(model):
    """
    Approximate Intel generation from model number.

    Examples:
    13420 -> 13
    1245  -> 12
    10210 -> 10
    8265  -> 8
    6500  -> 6
    """

    if len(model) == 5:
        return int(model[:2])

    if len(model) == 4:
        if model.startswith("10"):
            return 10

        return int(model[0])

    return 0

def score_ram(ram_gb):
    if ram_gb is None:
        return 0

    if ram_gb >= 64:
        return 25

    if ram_gb >= 32:
        return 25

    if ram_gb >= 24:
        return 23

    if ram_gb >= 16:
        return 20

    if ram_gb >= 8:
        return 10

    return 5


def score_storage(storage_gb):
    if storage_gb is None:
        return 0

    if storage_gb >= 2048:
        return 15

    if storage_gb >= 1024:
        return 15

    if storage_gb >= 512:
        return 12

    if storage_gb >= 256:
        return 7

    return 3


def score_gpu(gpu):
    if not gpu or gpu == "Unknown":
        return 0

    gpu_lower = gpu.lower()

    # Dedicated NVIDIA / AMD / Intel Arc
    if "rtx" in gpu_lower:
        return 5

    if "gtx" in gpu_lower:
        return 4

    if "radeon rx" in gpu_lower:
        return 4

    if "intel arc" in gpu_lower or gpu_lower.startswith("arc"):
        return 4

    # Integrated graphics
    if "iris xe" in gpu_lower:
        return 3

    if "radeon vega" in gpu_lower:
        return 3

    if "uhd" in gpu_lower:
        return 2

    return 1


def calculate_programming_score(product):
    cpu_score = score_cpu(product.get("cpu"))
    ram_score = score_ram(product.get("ram_gb"))
    storage_score = score_storage(product.get("storage_gb"))
    gpu_score = score_gpu(product.get("gpu"))

    total_score = (
        cpu_score
        + ram_score
        + storage_score
        + gpu_score
    )

    return {
        "programming_score": total_score,
        "programming_class": classify_programming_score(total_score),
        "cpu_score": cpu_score,
        "ram_score": ram_score,
        "storage_score": storage_score,
        "gpu_score": gpu_score,
    }

def classify_programming_score(score):
    if score >= 85:
        return "Excellent"

    if score >= 70:
        return "Good"

    if score >= 55:
        return "Acceptable"

    return "Poor"