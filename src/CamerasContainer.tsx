import { useState } from "react";

function CamerasContainer() {
  // this component shoul stack camera previews and allow to scroll them

  const [cameras] = useState(["cam0", "cam1", "cam2", "cam3", "cam4"]);

  return (
    <div id="cameras-container">
      {cameras.map((c, idx) => (
        <CameraView name={c} key={idx} />
      ))}
      <CameraViewAdd />
    </div>
  );
}

function CameraViewAdd() {
  return (
    <div className="camera-view" style={{ opacity: 0.5 }}>
      <span>
        {/* create a circle with plus sign inside */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            flexDirection: "column",
          }}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="feather feather-plus-circle"
          >
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="16"></line>
            <line x1="8" y1="12" x2="16" y2="12"></line>
          </svg>
          <span className="camera-view-add-text">Add camera</span>
        </div>
      </span>
    </div>
  );
}

function CameraView(props: { name: string }) {
  // this is a tile that should display a camera video preview, just like on a security guard's cctv monitor

  // Assuming the video source is related to the camera name, e.g., /videos/cam0.mp4
  // Replace with your actual video source logic
  const videoSrc = `/videos/${props.name}.mp4`;

  return (
    <div className="camera-view" style={{}}>
      <video
        src={videoSrc}
        autoPlay
        muted
        loop
        playsInline
        width="100%"
        height="100%"
        style={{ objectFit: "cover" }} // Ensures the video covers the area, might crop
        onError={(e) => {
          console.error(`Error loading video ${videoSrc}:`, e);
        }}
      >
        Your browser does not support the video tag.
      </video>
      {/* You can add an overlay with the camera name if needed */}
      {/* <div style={{ position: 'absolute', bottom: '5px', left: '5px', color: 'white', backgroundColor: 'rgba(0,0,0,0.5)', padding: '2px 5px' }}>
                                {props.name}
                        </div> */}
    </div>
  );
}

export default CamerasContainer;
