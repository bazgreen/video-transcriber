import whisper
import ffmpeg
import os
import re

def prompt_path():
    print("🔍 Enter the relative path to the folder with your video chunks:")
    path = input("📂 Path (e.g. dba/w1): ").strip()
    full_path = os.path.abspath(path)
    if not os.path.isdir(full_path):
        raise FileNotFoundError(f"❌ Directory not found: {full_path}")
    return full_path

def extract_audio_ffmpeg(video_path, audio_path):
    (
        ffmpeg
        .input(video_path)
        .output(audio_path, acodec='pcm_s16le', ac=1, ar='16000')
        .overwrite_output()
        .run(quiet=True)
    )

def transcribe_directory(video_dir):
    keywords = [
        "assignment", "submission", "deadline", "notebook", "python", "ipython",
        "output", "reference", "proof of concept", "automate", "RO1", "RO2", "RO3",
        "assessment", "grading", "criteria", "format", "feedback"
    ]

    model = whisper.load_model("small")
    output_dir = os.path.join(video_dir, "transcripts")
    os.makedirs(output_dir, exist_ok=True)

    all_transcripts = []
    all_highlights = []

    print(f"\n📁 Scanning for video chunks in {video_dir}...\n")

    for file in sorted(os.listdir(video_dir)):
        if file.startswith("w1_part_") and file.endswith(".mp4"):
            video_path = os.path.join(video_dir, file)
            base_name = os.path.splitext(file)[0]
            audio_path = os.path.join(video_dir, f"{base_name}.wav")

            print(f"🎧 Extracting audio: {file} → {base_name}.wav")
            extract_audio_ffmpeg(video_path, audio_path)

            print(f"🧠 Transcribing: {file}")
            result = model.transcribe(audio_path)
            transcript = result["text"]
            all_transcripts.append(f"\n\n--- {base_name} ---\n\n{transcript}")

            highlights = []
            for kw in keywords:
                pattern = re.compile(r".{0,50}" + re.escape(kw) + r".{0,50}", re.IGNORECASE)
                matches = pattern.findall(transcript)
                if matches:
                    highlights.append(f"\n🔹 Keyword: **{kw}**")
                    highlights.extend(matches)

            if highlights:
                all_highlights.append(f"\n\n--- {base_name} ---\n" + "\n".join(highlights))

            print(f"✅ Done: {file}")

    # Save full transcript
    with open(os.path.join(output_dir, "full_transcript.txt"), "w") as f:
        f.write("\n".join(all_transcripts))

    # Save assessment-related highlights
    with open(os.path.join(output_dir, "assessment_mentions.txt"), "w") as f:
        f.write("\n".join(all_highlights) if all_highlights else "No assessment-related content found.")

    # Generate basic summary
    summary_points = set()
    for h in all_highlights:
        for line in h.splitlines():
            if len(line.split()) > 5 and any(kw in line.lower() for kw in keywords):
                summary_points.add(line.strip())

    with open(os.path.join(output_dir, "summary.txt"), "w") as f:
        f.write("Summary of Assessment-Related Content:\n\n")
        for point in sorted(summary_points):
            f.write(f"- {point}\n")

    print(f"\n📄 Outputs saved to: {output_dir}")
    print("🟢 Process completed.\n")

if __name__ == "__main__":
    try:
        base_dir = prompt_path()
        transcribe_directory(base_dir)
    except Exception as e:
        print(f"\n❌ Error: {e}")

