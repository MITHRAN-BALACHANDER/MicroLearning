import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BarChart3, TrendingUp, Video, Star } from "lucide-react"
import { getVideoAnalytics, getUserEngagement } from "@/lib/adminApi"

export default function AnalyticsPage() {
  const [videoAnalytics, setVideoAnalytics] = useState<any>(null)
  const [userEngagement, setUserEngagement] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const [videoData, engagementData] = await Promise.all([
          getVideoAnalytics(),
          getUserEngagement(),
        ])
        setVideoAnalytics(videoData)
        setUserEngagement(engagementData)
      } catch (error) {
        console.error('Failed to fetch analytics:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchAnalytics()
  }, [])

  if (loading) {
    return (
      <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-48 bg-muted rounded" />
          <div className="grid gap-4 md:grid-cols-2">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i}>
                <CardHeader>
                  <div className="h-4 w-24 bg-muted rounded" />
                </CardHeader>
                <CardContent>
                  <div className="h-32 bg-muted rounded" />
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
          <p className="text-muted-foreground">
            Detailed analytics and insights about your platform
          </p>
        </div>

        {/* Top Rated Videos */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Star className="h-5 w-5" />
              Top Rated Videos
            </CardTitle>
            <CardDescription>
              Videos with highest average ratings
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {videoAnalytics?.topRatedVideos?.slice(0, 10).map((video: any, index: number) => (
                <div key={video.videoId} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Badge variant="secondary" className="w-8 h-8 rounded-full flex items-center justify-center">
                      {index + 1}
                    </Badge>
                    <div>
                      <p className="font-medium">{video.title}</p>
                      <p className="text-sm text-muted-foreground">
                        {video.totalRatings} ratings
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    <span className="font-semibold">{video.avgRating.toFixed(2)}</span>
                  </div>
                </div>
              )) || <p className="text-muted-foreground">No data available</p>}
            </div>
          </CardContent>
        </Card>

        {/* Videos by Category */}
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Video className="h-5 w-5" />
                Videos by Category
              </CardTitle>
              <CardDescription>
                Distribution of videos across categories
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {videoAnalytics?.videosByCategory?.map((cat: any) => (
                  <div key={cat._id} className="flex items-center justify-between">
                    <span className="font-medium">{cat.categoryName || "Uncategorized"}</span>
                    <Badge>{cat.count} videos</Badge>
                  </div>
                )) || <p className="text-muted-foreground">No data available</p>}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Rating Distribution
              </CardTitle>
              <CardDescription>
                User ratings breakdown
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {userEngagement?.ratingDistribution?.map((rating: any) => (
                  <div key={rating._id} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                      <span className="font-medium">{rating._id} Stars</span>
                    </div>
                    <Badge variant="secondary">{rating.count} ratings</Badge>
                  </div>
                )) || <p className="text-muted-foreground">No data available</p>}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* User Registration Trend */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              User Registration Trend
            </CardTitle>
            <CardDescription>
              Monthly user registration over the past year
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {userEngagement?.userTrend?.map((trend: any) => (
                <div key={`${trend._id.year}-${trend._id.month}`} className="flex items-center justify-between">
                  <span className="text-sm font-medium">
                    {new Date(trend._id.year, trend._id.month - 1).toLocaleDateString('en-US', { 
                      year: 'numeric', 
                      month: 'long' 
                    })}
                  </span>
                  <Badge variant="outline">{trend.count} users</Badge>
                </div>
              )) || <p className="text-muted-foreground">No data available</p>}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
