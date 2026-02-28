import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Paper,
  Typography,
} from "@mui/material";
import { useState } from "react";

interface BatchTabProps {
  apiUrl: string;
  apiKey: string;
}

export function BatchTab({ apiUrl, apiKey }: BatchTabProps) {
  const [batchFile, setBatchFile] = useState<File | null>(null);
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchError, setBatchError] = useState("");
  const [batchDownloadUrl, setBatchDownloadUrl] = useState("");
  const [batchPreview, setBatchPreview] = useState<string[]>([]);

  const handleBatch = async () => {
    if (!batchFile) {
      setBatchError("Please select a CSV file first.");
      return;
    }
    // Validate file size (10MB max)
    const maxSizeBytes = 10 * 1024 * 1024;
    if (batchFile.size > maxSizeBytes) {
      setBatchError("File is too large. Maximum size is 10 MB.");
      return;
    }
    setBatchError("");
    setBatchDownloadUrl("");
    setBatchPreview([]);
    setBatchLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", batchFile);
      const requestHeaders: Record<string, string> = {};
      if (apiKey.trim()) {
        requestHeaders["x-api-key"] = apiKey.trim();
      }
      const response = await fetch(`${apiUrl}/v1/batch`, {
        method: "POST",
        headers: requestHeaders,
        body: formData,
      });
      if (!response.ok) {
        const text = await response.text();
        let message =
          "Batch processing failed. Please check your file and try again.";
        try {
          const errorData = JSON.parse(text);
          if (errorData.detail) {
            message = errorData.detail;
          } else if (errorData.message) {
            message = errorData.message;
          }
        } catch {
          if (text) message = text;
        }
        throw new Error(message);
      }
      const text = await response.text();
      const lines = text.split(/\r?\n/).filter(Boolean);
      setBatchPreview(lines.slice(0, 6));
      const blob = new Blob([text], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      setBatchDownloadUrl(url);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Something went wrong. Please try again.";
      setBatchError(message);
    } finally {
      setBatchLoading(false);
    }
  };

  return (
    <Box display="grid" gap={2}>
      {/* Instructions */}
      <Alert severity="info" sx={{ mb: 1 }}>
        Upload a CSV file with a <code>text</code> column. Each row will be
        analyzed for malicious content.
        <br />
        <Typography variant="caption" sx={{ mt: 0.5, display: "block" }}>
          Maximum file size: 10 MB. Supported format: CSV with UTF-8 encoding.
        </Typography>
      </Alert>

      <Button
        variant="outlined"
        component="label"
        aria-label="Select a CSV file to upload"
      >
        {batchFile ? "Change File" : "Select CSV File"}
        <input
          type="file"
          accept=".csv"
          hidden
          onChange={(event) => {
            const file = event.target.files?.[0] ?? null;
            setBatchFile(file);
            setBatchError("");
            setBatchDownloadUrl("");
            setBatchPreview([]);
          }}
        />
      </Button>
      {batchFile && (
        <Typography variant="body2" color="text.secondary">
          Selected: {batchFile.name} ({(batchFile.size / 1024).toFixed(1)} KB)
        </Typography>
      )}
      <Box display="flex" alignItems="center" gap={2}>
        <Button
          variant="contained"
          onClick={handleBatch}
          disabled={!batchFile || batchLoading}
          aria-label="Run batch analysis"
        >
          {batchLoading ? "Processing..." : "Run Batch Analysis"}
        </Button>
        {batchLoading && (
          <CircularProgress size={24} aria-label="Processing batch file" />
        )}
      </Box>
      {batchError && (
        <Alert severity="error" onClose={() => setBatchError("")} role="alert">
          <strong>Batch Processing Failed:</strong> {batchError}
          <br />
          <Typography variant="caption" sx={{ mt: 1, display: "block" }}>
            Common issues: File too large (&gt;10MB), missing &apos;text&apos;
            column, or invalid CSV format.
          </Typography>
        </Alert>
      )}
      {batchPreview.length > 0 && (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Results Preview (first 5 rows)
          </Typography>
          {batchPreview.map((line, index) => (
            <Typography
              variant="body2"
              key={`${line}-${index}`}
              sx={{ fontFamily: "monospace", fontSize: "0.8rem" }}
            >
              {line}
            </Typography>
          ))}
        </Paper>
      )}
      {batchDownloadUrl && (
        <Button
          variant="outlined"
          href={batchDownloadUrl}
          download={`predictions_${batchFile?.name ?? "output.csv"}`}
          aria-label="Download analysis results"
        >
          Download Full Results
        </Button>
      )}
    </Box>
  );
}
