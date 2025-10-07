import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  CheckCircle2,
  Clock3,
  FileText,
  ShieldCheck,
  UploadCloud,
  VideoIcon,
  XCircle,
  Wand2,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";

const STATUS_META = {
  pending: {
    label: "Awaiting QA",
    badge: "secondary",
    icon: Clock3,
  },
  accepted: {
    label: "Approved",
    badge: "success",
    icon: CheckCircle2,
  },
  rejected: {
    label: "Changes requested",
    badge: "destructive",
    icon: XCircle,
  },
};

const INITIAL_NOTES =
  "Auto-generated description based on video content analysis. Replace with moderation notes once QA flow is wired.";

export default function UploadContent() {
  const navigate = useNavigate();
  const [category, setCategory] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [queue, setQueue] = useState([]);

  const handleUpload = () => {
    if (!category || !title || !file) return;

    setUploading(true);

    setTimeout(() => {
      const entry = {
        id: crypto.randomUUID(),
        title,
        category,
        description: description || INITIAL_NOTES,
        status: "pending",
        uploadedAt: new Date().toISOString(),
        filename: file.name,
      };
      setQueue((prev) => [entry, ...prev]);
      setUploading(false);
      setCategory("");
      setTitle("");
      setDescription("");
      setFile(null);
    }, 1600);

    // backend: replace timeout with POST /content/upload using multipart/form-data
    // FormData payload => { video: file, title, category, description }
  };

  const updateStatus = (id, status) => {
    setQueue((prev) =>
      prev.map((item) => (item.id === id ? { ...item, status } : item))
    );
    // backend: PATCH /content/:id/status with { status }
  };

  const formatTimestamp = (value) =>
    new Date(value).toLocaleString(undefined, {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });

  return (
    <section className="space-y-10">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-2">
          <Button
            variant="ghost"
            size="sm"
            className="gap-2 px-0"
            onClick={() => navigate("/content-management")}
          >
            <ArrowLeft className="h-4 w-4" />
            Back to library
          </Button>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              Video ingestion studio
            </h1>
            <p className="text-sm text-muted-foreground">
              Upload raw lessons, add metadata, and route them through the
              moderation workflow.
            </p>
          </div>
        </div>
        <Badge variant="outline" className="gap-2 text-xs">
          <ShieldCheck className="h-3 w-3" />
          Assets are scanned for malware.{" "}
          {/* backend: confirm AV scan status from upload response */}
        </Badge>
      </header>

      <Card className="border-border/70">
        <CardHeader className="space-y-2">
          <CardTitle className="flex items-center gap-2 text-lg font-semibold">
            <UploadCloud className="h-4 w-4" />
            Upload a new asset
          </CardTitle>
          <CardDescription>
            Provide a working title, categorize the resource, and attach the
            source file.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                placeholder="e.g. Navigating quarterly budgets"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <Input
                id="category"
                placeholder="Finance, Compliance, Leadership..."
                value={category}
                onChange={(event) => setCategory(event.target.value)}
                // backend: replace free text with select fed by GET /categories
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Moderator notes</Label>
              <Textarea
                id="description"
                placeholder="Optional context for reviewers"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                rows={4}
              />
            </div>
          </div>

          <div className="space-y-4">
            <Label>Source file</Label>
            <label
              htmlFor="file-upload"
              className={cn(
                "flex h-44 cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed border-muted-foreground/40 bg-muted/30 text-center transition hover:border-primary hover:bg-muted/50",
                file && "border-primary"
              )}
            >
              <Input
                id="file-upload"
                type="file"
                accept="video/*,application/pdf,application/vnd.ms-powerpoint,application/vnd.ms-excel,.doc,.docx"
                className="hidden"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
              <VideoIcon className="h-8 w-8 text-muted-foreground" />
              <div className="space-y-1 text-sm">
                <p className="font-medium">Drop file or browse</p>
                <p className="text-muted-foreground">
                  MP4, PDF, PPTX, XLSX up to 500 MB
                </p>
              </div>
              {file && <Badge variant="outline">{file.name}</Badge>}
            </label>
            <div className="rounded-md border bg-muted/30 p-3 text-xs text-muted-foreground">
              {/* backend: surface transcoding status once upload API responds */}
              We transcode uploads to adaptive bitrate streaming automatically.
            </div>
          </div>
        </CardContent>
        <CardFooter className="justify-end">
          <Button
            className="gap-2"
            disabled={uploading || !category || !title || !file}
            onClick={handleUpload}
          >
            {uploading ? (
              <>
                <Wand2 className="h-4 w-4 animate-spin" />
                Processing
              </>
            ) : (
              <>
                <UploadCloud className="h-4 w-4" />
                Upload & generate summary
              </>
            )}
          </Button>
        </CardFooter>
      </Card>

      <Card className="border-border/70">
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
            <CardTitle className="text-lg font-semibold">
              Review queue
            </CardTitle>
            <CardDescription>
              Track moderation state before publishing to the learner catalogue.
            </CardDescription>
          </div>
          <Badge variant="secondary">{queue.length} items</Badge>
        </CardHeader>
        <CardContent>
          {queue.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-muted-foreground/40 bg-muted/20 py-12 text-center">
              <VideoIcon className="h-8 w-8 text-muted-foreground" />
              <p className="text-sm font-medium">No uploads pending</p>
              <p className="text-xs text-muted-foreground">
                New submissions will appear here for editorial review.
              </p>
            </div>
          ) : (
            <ScrollArea className="max-h-[420px] pr-4">
              <div className="space-y-4">
                {queue.map((item) => {
                  const meta = STATUS_META[item.status];
                  const Icon = meta.icon;
                  return (
                    <div
                      key={item.id}
                      className="rounded-xl border border-border/80 bg-card/80 p-4 shadow-sm transition hover:border-primary"
                    >
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div className="space-y-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="text-sm font-semibold">
                              {item.title}
                            </p>
                            <Badge variant="outline" className="capitalize">
                              {item.category}
                            </Badge>
                            <Badge
                              variant={meta.badge}
                              className="gap-1 text-xs capitalize"
                            >
                              <Icon className="h-3 w-3" />
                              {meta.label}
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground">
                            Uploaded {formatTimestamp(item.uploadedAt)}
                            {item.filename ? ` • ${item.filename}` : ""}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {item.description}
                          </p>
                        </div>
                        {item.status === "pending" && (
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              className="gap-1"
                              onClick={() => updateStatus(item.id, "accepted")}
                            >
                              <CheckCircle2 className="h-4 w-4" />
                              Approve
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="gap-1"
                              onClick={() => updateStatus(item.id, "rejected")}
                            >
                              <XCircle className="h-4 w-4" />
                              Request edits
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </ScrollArea>
          )}
        </CardContent>
        <CardFooter className="flex flex-col gap-3 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <div>
            {/* backend: sync with background worker to reflect transcription or AI summary progress */}
            AI-powered transcripts attach automatically after approval.
          </div>
          <Button
            variant="outline"
            size="sm"
            className="gap-2"
            onClick={() => navigate("/analytics")}
          >
            <Wand2 className="h-3 w-3" />
            View ingestion analytics
          </Button>
        </CardFooter>
      </Card>
    </section>
  );
}
