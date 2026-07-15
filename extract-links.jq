def val($x):
  if ($x == null or $x == "") then null else $x end;

{
  schema_version: 1,
  generated_at: "2026-07-15",
  source: {
    app: "Fundamentos",
    endpoint: "https://api.fundamentos.me/api/edge/cycles",
    validation: "Estrutura e tipos de mídia conferidos no app via Espelhamento do iPhone"
  },
  summary: {
    cycle_count: 15,
    lesson_count: ([.cycles[:15][].lessons[]] | length)
  },
  cycles: [
    .cycles[:15][] |
    {
      id,
      number,
      title,
      active,
      lessons: [
        .lessons[] |
        {
          id,
          number,
          title,
          links: {
            video: {
              primary: val(.urlShortVideoS3 // .urlShortVideo),
              youtube_summary: val(.urlShortVideo),
              full_video: val(.urlVideoS3),
              original_live: val(.urlLive),
              sign_language: val(.urlSignLanguageVideo)
            },
            transcript_pdf: val(.printVersion_pt // .printVersion),
            podcasts: ([
              {
                platform: "Google Podcasts",
                summary: val(.urlGooglePodcastShort),
                full: val(.urlGooglePodcast)
              },
              {
                platform: "Spotify",
                summary: val(.urlSpotifyShort),
                full: val(.urlSpotify)
              },
              {
                platform: "Deezer",
                summary: val(.urlDeezerShort),
                full: val(.urlDeezer)
              },
              {
                platform: "Apple Podcasts",
                summary: val(.urlApplePodcastShort),
                full: val(.urlApplePodcast)
              }
            ] | map(select(.summary != null or .full != null)))
          }
        }
      ]
    }
  ]
}
