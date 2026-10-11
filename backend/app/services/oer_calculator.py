from typing import Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.schemas.schemas import OERCalculationResult

class OERCalculator:
    """
    Kalkulator estimasi Oil Extraction Rate (OER) dan Indeks Mutu TBS.
    
    CATATAN ILMIAH & METODOLOGI RISET:
    Koefisien rendemen fraksi (Unripe 12%, Underripe 17%, Ripe 23.5%, Overripe 21%)
    dan formula penalti mutu dalam modul ini merupakan formulasi baseline heuristik
    (preliminary placeholder) yang diturunkan dari literatur agronomi Wood et al. dan IOPRI (1997).
    Dalam implementasi riset lapangan BPDP, nilai-nilai parameter ini dirancang untuk
    dikalibrasi ulang secara empiris menggunakan data uji laboratorium ekstraksi Soxhlet
    di PKS mitra.
    """

    @classmethod
    def calculate(
        cls,
        counts: Dict[str, int],
        net_weight_kg: Optional[float] = None,
        base_price_per_kg: Optional[float] = None,
        baseline_oer: Optional[float] = None,
        long_stalk_count: int = 0
    ) -> OERCalculationResult:
        n_unripe = counts.get("unripe", 0)
        n_underripe = counts.get("underripe", 0)
        n_ripe = counts.get("ripe", 0)
        n_overripe = counts.get("overripe", 0)
        n_empty = counts.get("empty_bunch", 0)
        n_abnormal = counts.get("abnormal", 0)
        n_stalk = counts.get("long_stalk", long_stalk_count)
        
        total = n_unripe + n_underripe + n_ripe + n_overripe + n_empty + n_abnormal
        if total == 0:
            p_unripe = p_underripe = p_ripe = p_overripe = p_empty = p_abnormal = p_stalk = 0.0
        else:
            p_unripe = (n_unripe / total) * 100.0
            p_underripe = (n_underripe / total) * 100.0
            p_ripe = (n_ripe / total) * 100.0
            p_overripe = (n_overripe / total) * 100.0
            p_empty = (n_empty / total) * 100.0
            p_abnormal = (n_abnormal / total) * 100.0
            p_stalk = (n_stalk / total) * 100.0

        # 1. Estimasi OER Terbobot
        if total == 0:
            estimated_oer = settings.BASELINE_OER_BENCHMARK
        else:
            w_unripe = settings.OER_YIELD_UNRIPE
            w_underripe = settings.OER_YIELD_UNDERRIPE
            w_ripe = settings.OER_YIELD_RIPE
            w_overripe = settings.OER_YIELD_OVERRIPE
            
            # (fraction * weight) * 100
            estimated_oer = (
                (p_unripe / 100.0 * w_unripe) +
                (p_underripe / 100.0 * w_underripe) +
                (p_ripe / 100.0 * w_ripe) +
                (p_overripe / 100.0 * w_overripe)
            ) * 100.0

        target_baseline = baseline_oer or settings.BASELINE_OER_BENCHMARK
        oer_variance = estimated_oer - target_baseline

        # 2. Indeks Kualitas Mutu TBS (0.0 - 1.0)
        if total == 0:
            quality_score = 1.0
        else:
            quality_score = (
                (1.0 * n_ripe) +
                (0.7 * n_underripe) +
                (0.4 * n_overripe) +
                (0.0 * n_unripe)
            ) / total

        # 3. Kategori Risiko FFA (Free Fatty Acid)
        if p_overripe > 15.0:
            ffa_risk = "HIGH"
        elif p_overripe > 8.0:
            ffa_risk = "MEDIUM"
        else:
            ffa_risk = "LOW"

        # 4. Potongan / Penalti Harga TBS (% potongan harga beli)
        # Toleransi buah mentah = 0% -> setiap 1% buah mentah kena penalti 1%
        penalty_unripe = p_unripe * 1.0
        # Toleransi buah kurang matang = 5% -> kelebihan dikenakan penalti 0.5%
        penalty_underripe = max(0.0, p_underripe - 5.0) * 0.5
        # Buah overripe > 10% dikenakan risiko penalti FFA 0.3%
        penalty_overripe = max(0.0, p_overripe - 10.0) * 0.3

        total_penalty_pct = min(50.0, penalty_unripe + penalty_underripe + penalty_overripe)

        # 5. Potongan Berat Tangkai Panjang (> 2.5 cm)
        # Standar PKS: Toleransi tangkai panjang 2%. Kelebihan dikenakan potongan berat 1:1
        stalk_penalty_pct = max(0.0, p_stalk - 2.0) * 1.0
        stalk_penalty_pct = min(15.0, stalk_penalty_pct)

        # 6. Kalkulasi Harga Beli Bersih
        base_price = base_price_per_kg or settings.DEFAULT_TBS_PRICE_PER_KG
        final_price = max(500.0, base_price * (1.0 - (total_penalty_pct / 100.0)))

        # 7. Bobot Bersih Efektif & Total Pembayaran
        effective_net_weight = None
        total_payout = None
        if net_weight_kg and net_weight_kg > 0:
            effective_net_weight = net_weight_kg * (1.0 - (stalk_penalty_pct / 100.0))
            total_payout = effective_net_weight * final_price

        return OERCalculationResult(
            total_bunches=total,
            unripe_count=n_unripe,
            underripe_count=n_underripe,
            ripe_count=n_ripe,
            overripe_count=n_overripe,
            empty_bunch_count=n_empty,
            abnormal_count=n_abnormal,
            long_stalk_count=n_stalk,
            unripe_percentage=round(p_unripe, 2),
            underripe_percentage=round(p_underripe, 2),
            ripe_percentage=round(p_ripe, 2),
            overripe_percentage=round(p_overripe, 2),
            empty_bunch_percentage=round(p_empty, 2),
            abnormal_percentage=round(p_abnormal, 2),
            long_stalk_percentage=round(p_stalk, 2),
            estimated_oer_percentage=round(estimated_oer, 2),
            baseline_oer_percentage=round(target_baseline, 2),
            oer_variance=round(oer_variance, 2),
            quality_score=round(quality_score, 3),
            price_per_kg_base=round(base_price, 2),
            price_penalty_percentage=round(total_penalty_pct, 2),
            stalk_penalty_percentage=round(stalk_penalty_pct, 2),
            effective_net_weight_kg=round(effective_net_weight, 2) if effective_net_weight is not None else None,
            final_price_per_kg=round(final_price, 2),
            total_payout=round(total_payout, 2) if total_payout is not None else None,
            ffa_risk_category=ffa_risk
        )
