#!/usr/bin/env python3
"""Local media -> timestamped SRT/TXT transcript."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


SUITE_DIR = Path(__file__).resolve().parents[3]
AUDIO_EXTS = {".aac", ".aiff", ".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav", ".webm", ".wma"}
VIDEO_EXTS = {".avi", ".flv", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".webm", ".wmv"}
SENTENCE_END = ".?!。？！…"
SOFT_BREAK = ",;:，；：、"


class MissingEngine(Exception):
    pass


class TranscriptionError(Exception):
    pass


class Word:
    def __init__(self, start: float, end: float, word: str) -> None:
        self.start = start
        self.end = end
        self.word = word


class Segment:
    def __init__(self, start: float, end: float, text: str, words: list[Word] | None = None) -> None:
        self.start = start
        self.end = end
        self.text = text
        self.words = words or []


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def make_job_id() -> str:
    return f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"


def load_config() -> dict:
    config_path = SUITE_DIR / "config.json"
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text(encoding="utf-8"))


def resolve_output_root(args: argparse.Namespace) -> Path:
    config = load_config()
    value = args.output_dir or config.get("output_dir") or str(SUITE_DIR / "runs")
    root = Path(value).expanduser()
    if not root.is_absolute():
        root = (Path.cwd() / root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


class RunRecord:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.job_id = make_job_id()
        self.created_at = now_iso()
        self.run_dir = resolve_output_root(args) / self.job_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.run_dir / "run.log"
        self.manifest_path = self.run_dir / "manifest.json"
        self.errors: list[dict] = []
        self.warnings: list[dict] = []
        self.outputs: dict = {
            "run_dir": str(self.run_dir),
            "manifest_path": str(self.manifest_path),
            "log_path": str(self.log_path),
        }

    def log(self, message: str) -> None:
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(f"[{now_iso()}] {message}\n")

    def write_manifest(self, status: str) -> None:
        manifest = {
            "job_id": self.job_id,
            "skill": "vlp-speech-transcribe",
            "status": status,
            "input": {
                "value": self.args.input,
                "engine": self.args.engine,
                "language": self.args.language,
            },
            "outputs": self.outputs,
            "warnings": self.warnings,
            "errors": self.errors,
            "created_at": self.created_at,
            "completed_at": now_iso(),
        }
        self.manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def fail(self, code: str, message: str) -> int:
        self.errors.append({"code": code, "message": message})
        self.log(f"ERROR {code}: {message}")
        self.write_manifest("failed")
        print(f"failed: {message}", file=sys.stderr)
        print(f"manifest: {self.manifest_path}", file=sys.stderr)
        print(f"log: {self.log_path}", file=sys.stderr)
        return 1


def resolve_input(value: str) -> tuple[Path, str]:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    if not path.exists():
        return path, "missing"
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        outputs = data.get("outputs", {})
        media = outputs.get("output_file_path") or outputs.get("source_path")
        if not media:
            raise ValueError("manifest does not contain outputs.output_file_path or outputs.source_path")
        media_path = Path(media).expanduser()
        if not media_path.is_absolute():
            media_path = (path.parent / media_path).resolve()
        return media_path, "manifest"
    return path, "local"


def media_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in VIDEO_EXTS:
        return "video"
    if suffix in AUDIO_EXTS:
        return "audio"
    return "audio"


def extract_audio(video_path: Path, wav_path: Path, run: RunRecord) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise FileNotFoundError("ffmpeg is not installed or not on PATH")
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(wav_path),
    ]
    run.outputs["audio_extract_command"] = " ".join(cmd)
    run.log(f"extract audio: {' '.join(cmd)}")
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    with run.log_path.open("a", encoding="utf-8") as f:
        f.write(proc.stdout or "")
        if proc.stdout and not proc.stdout.endswith("\n"):
            f.write("\n")
    return proc.returncode == 0 and wav_path.exists()


def format_timestamp(seconds: float) -> str:
    ms_total = max(0, int(round(seconds * 1000)))
    ms = ms_total % 1000
    total_seconds = ms_total // 1000
    s = total_seconds % 60
    total_minutes = total_seconds // 60
    m = total_minutes % 60
    h = total_minutes // 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def flush_words(words: list[Word]) -> dict | None:
    text = "".join(word.word for word in words).strip()
    if not text:
        return None
    return {"start": words[0].start, "end": words[-1].end, "text": text}


def find_soft_cut(words: list[Word]) -> int | None:
    for index in range(len(words) - 1, -1, -1):
        text = words[index].word.strip()
        if text and text[-1] in SOFT_BREAK:
            return index
    return None


def find_pause_cut(words: list[Word], min_gap: float = 0.2) -> int | None:
    best_gap = min_gap
    best_index = None
    start = max(1, len(words) // 3)
    for index in range(start, len(words) - 1):
        gap = words[index + 1].start - words[index].end
        if gap > best_gap:
            best_gap = gap
            best_index = index
    return best_index


def postprocess_segments(segments: list[dict]) -> list[dict]:
    cleaned = []
    for item in segments:
        if item["end"] <= item["start"]:
            continue
        if cleaned and item["text"] == cleaned[-1]["text"]:
            cleaned[-1]["end"] = max(cleaned[-1]["end"], item["end"])
            continue
        cleaned.append(item)

    merged = []
    for item in cleaned:
        duration = item["end"] - item["start"]
        if merged and duration < 0.4 and len(item["text"].split()) < 3:
            merged[-1]["end"] = item["end"]
            merged[-1]["text"] += " " + item["text"]
        else:
            merged.append(item)

    for index in range(1, len(merged)):
        if merged[index]["start"] < merged[index - 1]["end"]:
            merged[index]["start"] = merged[index - 1]["end"]
        if merged[index]["end"] <= merged[index]["start"]:
            merged[index]["end"] = merged[index]["start"] + 0.3
    return merged


def merge_words_to_segments(
    segments: list[Segment],
    max_line_ms: int = 6000,
    pause_ms: int = 500,
    max_chars: int = 80,
) -> list[dict]:
    flat: list[Word] = []
    for segment in segments:
        if segment.words:
            flat.extend(segment.words)
        else:
            flat.append(Word(segment.start, segment.end, segment.text))
    if not flat:
        return []

    result = []
    current: list[Word] = []
    for index, word in enumerate(flat):
        current.append(word)
        word_text = word.word.strip()
        current_text = "".join(item.word for item in current).strip()
        duration_ms = (word.end - current[0].start) * 1000
        gap_ms = ((flat[index + 1].start - word.end) * 1000) if index + 1 < len(flat) else 0

        if (word_text and word_text[-1] in SENTENCE_END) or gap_ms >= pause_ms:
            item = flush_words(current)
            if item:
                result.append(item)
            current = []
        elif duration_ms >= max_line_ms or len(current_text) >= max_chars:
            cut = find_soft_cut(current)
            if cut is None or cut >= len(current) - 1:
                cut = find_pause_cut(current)
            if cut is not None and cut < len(current) - 1:
                head, current = current[: cut + 1], current[cut + 1 :]
                item = flush_words(head)
                if item:
                    result.append(item)
            else:
                item = flush_words(current)
                if item:
                    result.append(item)
                current = []

    if current:
        item = flush_words(current)
        if item:
            result.append(item)
    return postprocess_segments(result)


def transcribe_mlx(audio_path: Path, language: str | None) -> tuple[list[Segment], dict]:
    try:
        import mlx_whisper
    except ImportError as exc:
        raise MissingEngine("mlx-whisper is not installed") from exc

    kwargs = {"path_or_hf_repo": "mlx-community/whisper-large-v3-turbo", "word_timestamps": True}
    if language:
        kwargs["language"] = language
    try:
        result = mlx_whisper.transcribe(str(audio_path), **kwargs)
    except Exception as exc:  # pragma: no cover - depends on external engine/runtime
        raise TranscriptionError(f"mlx-whisper failed: {exc}") from exc

    converted = []
    for item in result.get("segments", []):
        words = [Word(w["start"], w["end"], w.get("word", "")) for w in item.get("words", [])]
        converted.append(Segment(item["start"], item["end"], item.get("text", ""), words))
    return converted, {"engine": "mlx", "detected_language": result.get("language")}


def transcribe_faster(audio_path: Path, language: str | None, model_name: str) -> tuple[list[Segment], dict]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise MissingEngine("faster-whisper is not installed") from exc

    try:
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
        kwargs = {"word_timestamps": True}
        if language:
            kwargs["language"] = language
        segments_iter, info = model.transcribe(str(audio_path), **kwargs)
        return list(segments_iter), {
            "engine": "faster",
            "detected_language": getattr(info, "language", None),
            "language_probability": getattr(info, "language_probability", None),
        }
    except Exception as exc:  # pragma: no cover - depends on external engine/runtime
        raise TranscriptionError(f"faster-whisper failed: {exc}") from exc


def transcribe_audio(run: RunRecord, audio_path: Path) -> tuple[list[Segment], dict] | None:
    requested = run.args.engine
    engines = ["mlx", "faster"] if requested == "auto" else [requested]
    for engine in engines:
        run.log(f"try engine: {engine}")
        try:
            if engine == "mlx":
                segments, meta = transcribe_mlx(audio_path, run.args.language)
            else:
                segments, meta = transcribe_faster(audio_path, run.args.language, run.args.model)
            run.outputs["engine_used"] = meta.get("engine")
            run.outputs["detected_language"] = meta.get("detected_language")
            if meta.get("language_probability") is not None:
                run.outputs["language_probability"] = meta["language_probability"]
            return segments, meta
        except (MissingEngine, TranscriptionError) as exc:
            run.warnings.append({"code": f"{engine}_unavailable", "message": str(exc)})
            run.log(f"WARNING {engine}_unavailable: {exc}")
    return None


def write_outputs(segments: list[dict], srt_path: Path, txt_path: Path) -> None:
    with srt_path.open("w", encoding="utf-8") as srt:
        for index, segment in enumerate(segments, 1):
            srt.write(f"{index}\n")
            srt.write(f"{format_timestamp(segment['start'])} --> {format_timestamp(segment['end'])}\n")
            srt.write(f"{segment['text']}\n\n")
    txt_path.write_text("\n".join(segment["text"] for segment in segments).strip() + "\n", encoding="utf-8")


def run_transcribe(args: argparse.Namespace) -> int:
    run = RunRecord(args)
    run.log("run created")
    try:
        input_path, input_kind = resolve_input(args.input)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return run.fail("input_manifest_invalid", str(exc))

    if not input_path.exists():
        return run.fail("input_not_found", f"Input file does not exist: {input_path}")
    if not input_path.is_file():
        return run.fail("input_not_file", f"Input path is not a file: {input_path}")

    kind = media_kind(input_path)
    run.outputs.update({"input_path": str(input_path), "input_source": input_kind, "input_media_type": kind})
    audio_path = input_path

    if kind == "video":
        audio_path = run.run_dir / "audio.wav"
        try:
            ok = extract_audio(input_path, audio_path, run)
        except FileNotFoundError as exc:
            return run.fail("missing_dependency", str(exc))
        if not ok:
            return run.fail("audio_extract_failed", "ffmpeg failed to extract audio")
        run.outputs["extracted_audio_path"] = str(audio_path)

    result = transcribe_audio(run, audio_path)
    if result is None:
        return run.fail(
            "missing_asr_engine",
            "No usable ASR engine. Install mlx-whisper or faster-whisper; dependencies were not installed automatically.",
        )

    raw_segments, _meta = result
    srt_segments = merge_words_to_segments(raw_segments, max_line_ms=args.max_line_ms, pause_ms=args.pause_ms)
    if not srt_segments:
        return run.fail("empty_transcript", "ASR completed but produced no transcript segments.")

    base = Path(args.output).stem if args.output else "transcript"
    srt_path = run.run_dir / f"{base}.srt"
    txt_path = run.run_dir / f"{base}.txt"
    write_outputs(srt_segments, srt_path, txt_path)
    run.outputs.update(
        {
            "srt_path": str(srt_path),
            "txt_path": str(txt_path),
            "segment_count": len(srt_segments),
            "max_line_ms": args.max_line_ms,
            "pause_ms": args.pause_ms,
        }
    )
    run.write_manifest("success")
    print(f"success: wrote {srt_path}")
    print(f"manifest: {run.manifest_path}")
    return 0


def self_check() -> int:
    segments = [
        Segment(0.0, 2.0, "", [Word(0.0, 0.2, "Hello"), Word(0.25, 0.5, " world."), Word(1.2, 1.5, " Again")]),
        Segment(1.6, 1.9, " Again"),
    ]
    merged = merge_words_to_segments(segments, max_line_ms=6000, pause_ms=500)
    assert len(merged) == 2
    assert merged[0]["text"] == "Hello world."
    assert merged[1]["start"] >= merged[0]["end"]

    with tempfile.TemporaryDirectory() as tmp:
        srt_path = Path(tmp) / "out.srt"
        txt_path = Path(tmp) / "out.txt"
        write_outputs(merged, srt_path, txt_path)
        srt = srt_path.read_text(encoding="utf-8")
        assert "00:00:00,000 --> 00:00:00,500" in srt
        assert txt_path.read_text(encoding="utf-8").strip().splitlines() == ["Hello world.", "Again Again"]
    print("self-check ok")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local audio/video -> timestamped SRT/TXT transcript.")
    parser.add_argument("input", nargs="?", help="Local audio/video path or media ingest manifest path.")
    parser.add_argument("--output-dir", help="Root directory for per-run output directories.")
    parser.add_argument("--output", default="transcript", help="Output basename inside the run dir.")
    parser.add_argument("--engine", choices=["auto", "mlx", "faster"], default="auto", help="ASR engine.")
    parser.add_argument("--model", default="large-v3-turbo", help="faster-whisper model name.")
    parser.add_argument("--language", default=None, help="Optional language code, such as en, zh, ja.")
    parser.add_argument("--max-line-ms", type=int, default=6000, help="Maximum subtitle segment duration.")
    parser.add_argument("--pause-ms", type=int, default=500, help="Word gap that triggers a segment break.")
    parser.add_argument("--self-check", action="store_true", help="Run local checks without ASR or ffmpeg.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_check:
        return self_check()
    if not args.input:
        parser.error("input is required unless --self-check is used")
    return run_transcribe(args)


if __name__ == "__main__":
    raise SystemExit(main())
