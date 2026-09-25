// macOS Vision metin tanima: PNG -> JSON (her gozlem: metin, guven, kutu piksel).
// Taranmis DIE kitaplarinda metin katmaninin yanina IKINCI, bagimsiz bir okuma
// icin (bkz. extract_mahalli_1984.py). Dil duzeltmesi kapali: rakamlar oldugu
// gibi okunur.
//
// Derleme:  swiftc -O vision_ocr.swift -o vision_ocr
// Kullanim: vision_ocr a.png b.png ...   (her biri icin a.png.json yazar)
import AppKit
import Foundation
import Vision

func oku(_ path: String) throws -> [String: Any] {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        throw NSError(domain: "vision_ocr", code: 1, userInfo: [NSLocalizedDescriptionKey: "okunamadi: \(path)"])
    }
    let W = Double(cg.width), H = Double(cg.height)
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = false
    req.recognitionLanguages = ["tr-TR", "en-US"]
    req.minimumTextHeight = 0.0
    try VNImageRequestHandler(cgImage: cg, options: [:]).perform([req])
    var out: [[String: Any]] = []
    for obs in req.results ?? [] {
        for c in obs.topCandidates(3) {
            let b = obs.boundingBox
            out.append(["text": c.string, "conf": c.confidence,
                        "box": [b.minX * W, (1 - b.maxY) * H, b.maxX * W, (1 - b.minY) * H]])
        }
    }
    return ["w": W, "h": H, "obs": out]
}

for path in CommandLine.arguments.dropFirst() {
    do {
        let data = try JSONSerialization.data(withJSONObject: try oku(path), options: [.sortedKeys])
        try data.write(to: URL(fileURLWithPath: path + ".json"))
    } catch {
        FileHandle.standardError.write("\(error.localizedDescription)\n".data(using: .utf8)!)
        exit(1)
    }
}
