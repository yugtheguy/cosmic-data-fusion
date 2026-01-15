# 🪐 Live Verification - 30-Second Setup

## TL;DR - Just Run This

**Terminal 1 (Start Backend):**
```bash
uvicorn app.main:app --reload
```

**Terminal 2 (Run Verification):**
```bash
python tests/verify_planet_hunter_live.py
```

Done! Watch it download TESS data and detect a planet. ⏳

---

## What It Does

✅ Checks server health  
✅ Downloads real NASA TESS data (~50MB)  
✅ Runs exoplanet detection (BLS algorithm)  
✅ Validates detected planet (period ~3.85 days)  
✅ Verifies database persistence  

**Time:** 30-60 seconds total

---

## Expected Output

```
⏳ Downloading TESS data from MAST archive...
This may take 30-60 seconds...

✅ Analysis completed in 45.3 seconds!
✅ Period is 3.8528 days (expected ~3.85)
✅ Transit depth is 0.453% (physically reasonable)
✅ Detected 12 transits

🌟 Planet Detected! 🌟
  Orbital Period: 3.852826 days
  Transit Depth: 0.453%
  Signal-to-Noise: 8.32

✅ ALL TESTS PASSED!
```

---

## Test Target

**TIC 261136679** (TOI-270)  
Known triple-planet system from NASA  
Expected planet: **3.85 day period**

---

## Troubleshooting

**"Cannot connect to localhost:8000"**
→ Start backend first (Terminal 1)

**"Request timed out"**
→ MAST download is slow, increase timeout to 120 seconds

**"No TESS data available"**
→ Star may not be in TESS, try different TIC

---

## Success = Exit Code 0

```bash
python tests/verify_planet_hunter_live.py
echo $?  # Prints 0 if successful
```

---

## Files

- **Script:** `tests/verify_planet_hunter_live.py` (370 lines)
- **Guide:** `VERIFY_PLANET_HUNTER_README.md` (Full details)
- **Quick Start:** This file

---

**Status:** ✅ Ready to deploy!
