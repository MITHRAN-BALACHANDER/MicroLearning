import { useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, MessageSquareText, TestTubeDiagonal } from "lucide-react";

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
import { Separator } from "@/components/ui/separator";

const MOCK_VIDEOS = [
  {
    id: "budgeting101",
    title: "Art of Budgeting",
    src: "/videos/sample.mp4",
    description: "Learn how to manage your finances.",
    tags: ["finance", "essentials"],
    duration: "08:34",
    suggestion: "Write down monthly expenses.",
    coachNotes: "Highlight recurring expenses during onboarding.",
    lastReviewedBy: "A. Sharma",
    lastReviewedOn: "2025-09-16",
    // backend: fetch from GET /content/:videoId
  },
  {
    id: "invest101",
    title: "Investing Basics",
    src: "/videos/sample.mp4",
    description: "Start your investment journey.",
    tags: ["finance", "portfolio"],
    duration: "14:10",
    suggestion: "Start with mutual funds or SIPs.",
    coachNotes: "Add example of market volatility.",
    lastReviewedBy: "M. Patel",
    lastReviewedOn: "2025-08-02",
  },
  {
    id: "startup101",
    title: "Starting a Startup",
    src: "/videos/sample.mp4",
    description: "Steps to launch your startup.",
    tags: ["business", "growth"],
    duration: "12:47",
    suggestion: "Validate your idea before building.",
    coachNotes: "Link to ideation toolkit.",
    lastReviewedBy: "C. Huang",
    lastReviewedOn: "2025-06-24",
  },
];

export default function Content() {
  const { videoId } = useParams();
  const navigate = useNavigate();

  const video = useMemo(
    () => MOCK_VIDEOS.find((item) => item.id === videoId),
    [videoId]
  );

  if (!video) {
    return (
      <div className="flex h-96 flex-col items-center justify-center space-y-4 text-center">
        <p className="text-lg font-semibold text-destructive">
          Video not found
        </p>
        <p className="text-sm text-muted-foreground">
          {/* backend: handle 404 from API by redirecting to library */}
          The requested content isnt available. It may have been archived or
          removed.
        </p>
        <Button variant="outline" onClick={() => navigate(-1)}>
          Return to library
        </Button>
      </div>
    );
  }

  return (
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(-1)}
          className="gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
        <Badge variant="secondary" className="capitalize">
          {video.tags[0]}
        </Badge>
      </div>

      <Card className="overflow-hidden border-border/70">
        <CardHeader className="space-y-3">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle className="text-xl font-semibold">
                {video.title}
              </CardTitle>
              <CardDescription>{video.description}</CardDescription>
            </div>
            <Badge variant="outline" className="gap-2 text-xs">
              <TestTubeDiagonal className="h-3 w-3" />
              {video.duration}
            </Badge>
          </div>
          <div className="flex flex-wrap gap-2">
            {video.tags.map((tag) => (
              <Badge key={tag} variant="outline" className="capitalize">
                {tag}
              </Badge>
            ))}
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="aspect-video overflow-hidden rounded-xl bg-muted">
            <video
              className="h-full w-full object-cover"
              src={video.src}
              controls
              // backend: stream from CDN or signed URL returned by backend
            />
          </div>

          <div className="grid gap-4 md:grid-cols-[2fr,1fr]">
            <div className="space-y-3">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                Facilitator notes
              </h2>
              <p className="text-sm text-muted-foreground">
                {video.suggestion}
              </p>
              <p className="text-sm text-muted-foreground">
                {video.coachNotes}
              </p>
            </div>
            <div className="rounded-lg border bg-muted/40 p-4 text-sm">
              <p className="font-medium">Last reviewed</p>
              <p className="text-muted-foreground">
                {video.lastReviewedOn} — {video.lastReviewedBy}
              </p>
              <Separator className="my-3" />
              <Button variant="outline" size="sm" className="w-full gap-2">
                <MessageSquareText className="h-4 w-4" />
                Start feedback session
                {/* backend: deep-link to conversation thread for this video */}
              </Button>
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex flex-wrap gap-2 border-t bg-muted/30 px-6 py-4">
          <Button variant="secondary" className="gap-2">
            <TestTubeDiagonal className="h-4 w-4" />
            Launch assessment
            {/* backend: trigger POST /tests to create practice quiz */}
          </Button>
          <Button variant="outline" className="gap-2">
            <MessageSquareText className="h-4 w-4" />
            Review feedback log
            {/* backend: navigate to /feedback/:videoId showing aggregated comments */}
          </Button>
        </CardFooter>
      </Card>
    </section>
  );
}
