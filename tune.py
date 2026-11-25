"""Vòng lặp tinh chỉnh (coordinate ascent) tham số tiền xử lý + Tesseract
để tối đa hóa độ chính xác đo được trên testset, lặp lại nhiều vòng."""
import json
from dataclasses import replace

from evaluate import evaluate, load_ground_truth
from pipeline import Config

PARAM_GRID = {
    "upscale": [1, 2, 3],
    "denoise": ["none", "median", "nlmeans"],
    "threshold": ["none", "otsu", "adaptive"],
    "deskew": [False, True],
    "psm": [3, 4, 6, 7],
}

ROUNDS = 2


def search_subset(all_filenames, step=3):
    # lấy 1/step số câu (đủ cả 4 biến thể) để dò nhanh, đánh giá cuối cùng mới dùng full set
    by_sentence = {}
    for fn in all_filenames:
        idx = int(fn.split("_")[0])
        by_sentence.setdefault(idx, []).append(fn)
    chosen = []
    for idx in sorted(by_sentence)[::step]:
        chosen.extend(by_sentence[idx])
    return chosen


def main():
    gt_map = load_ground_truth()
    all_filenames = list(gt_map.keys())
    subset = search_subset(all_filenames, step=3)
    print(f"Dùng {len(subset)}/{len(all_filenames)} ảnh để dò tham số (coordinate ascent).")

    current = Config()
    baseline = evaluate(current, filenames=subset)["char_accuracy"]
    print(f"Baseline (subset) char_accuracy = {baseline:.2%}  cfg={current.as_dict()}")

    history = [{"round": 0, "param": "baseline", "value": None, "char_accuracy": baseline, "cfg": current.as_dict()}]
    best_score = baseline

    for round_idx in range(1, ROUNDS + 1):
        improved_this_round = False
        for param, values in PARAM_GRID.items():
            best_value = getattr(current, param)
            best_value_score = best_score
            for value in values:
                if value == getattr(current, param):
                    continue
                trial_cfg = replace(current, **{param: value})
                score = evaluate(trial_cfg, filenames=subset)["char_accuracy"]
                print(f"  round {round_idx} | thử {param}={value!r} -> {score:.2%}")
                if score > best_value_score:
                    best_value_score = score
                    best_value = value
            if best_value != getattr(current, param):
                current = replace(current, **{param: best_value})
                best_score = best_value_score
                improved_this_round = True
                print(f"-> Cập nhật {param} = {best_value!r} (char_accuracy={best_score:.2%})")
            history.append({
                "round": round_idx, "param": param, "value": best_value,
                "char_accuracy": best_score, "cfg": current.as_dict(),
            })
        if not improved_this_round:
            print(f"Vòng {round_idx}: không còn cải thiện, dừng sớm.")
            break

    print("\n=== Cấu hình tốt nhất tìm được (trên subset) ===")
    print(current.as_dict(), f"char_accuracy(subset)={best_score:.2%}")

    print("\nĐánh giá lại trên TOÀN BỘ testset (80 ảnh)...")
    full_result = evaluate(current, filenames=all_filenames)
    print(f"Char accuracy (full): {full_result['char_accuracy']:.2%}")
    print(f"Word accuracy (full): {full_result['word_accuracy']:.2%}")
    print("Theo biến thể:", {k: f"{v:.2%}" for k, v in full_result["per_variant"].items()})

    with open("tune_result.json", "w", encoding="utf-8") as f:
        json.dump({
            "best_config": current.as_dict(),
            "subset_char_accuracy": best_score,
            "full_result": full_result,
            "history": history,
        }, f, ensure_ascii=False, indent=2)
    print("\nĐã lưu kết quả vào tune_result.json")


if __name__ == "__main__":
    main()
