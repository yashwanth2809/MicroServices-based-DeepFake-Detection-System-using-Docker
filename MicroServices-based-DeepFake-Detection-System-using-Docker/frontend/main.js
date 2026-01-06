window.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('uploadForm');
  const fileInput = document.getElementById('fileInput');
  const resultDiv = document.getElementById('result');

  function showSnowfall(duration = 6000) {
    tsParticles
      .load("snow-overlay", {
        fullScreen: { enable: false },
        particles: {
          number: { value: 60, density: { enable: true, area: 800 } },
          shape: {
            type: "image",
            image: {
              src: "/static/assets/snowflake.png",
              width: 32,
              height: 32
            }
          },
          opacity: { value: 0.8, random: { enable: true, minimumValue: 0.4 } },
          size: { value: { min: 20, max: 35 }, random: { enable: true, minimumValue: 10 } },
          move: { enable: true, direction: "bottom", speed: { min: 2, max: 5 }, outModes: { default: "out" } },
          rotate: { value: { min: 0, max: 360 }, direction: "random", animation: { enable: true, speed: 10 } }
        },
        detectRetina: true
      })
      .then(container => setTimeout(() => container.destroy(), duration));
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!fileInput.files.length) {
      alert('Please choose a file to analyze.');
      return;
    }

    resultDiv.innerHTML = '<p>🔍 Analyzing… Please wait.</p>';
    resultDiv.style.color = '#333';

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
      const resp = await fetch('/predict_all', { method: 'POST', body: formData });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
      const data = await resp.json();

      console.log("Raw API response:", data);

      if (!data || !data.file_type || !data.prediction) {
        throw new Error("Invalid prediction data");
      }

      let label, confidence;

      // 1) Image or Audio
      if (data.file_type === 'image' || data.file_type === 'audio') {
        label = data.prediction.label.toLowerCase();
        confidence = data.prediction.confidence;
      }

      // 2) Video (silent or with audio)
      else if (data.file_type === 'video') {
        const { final: finalLabel, video: v, audio: a } = data.prediction;

        if (typeof finalLabel !== 'string') {
          throw new Error("Invalid video prediction format");
        }

        label = finalLabel.toLowerCase();

        const vidConf = v?.confidence ?? 0;
        const audConf = a?.confidence;
        confidence = (audConf != null)
          ? (vidConf + audConf) / 2
          : vidConf;
      }

      // 3) Unknown
      else {
        throw new Error(`Unsupported file_type: ${data.file_type}`);
      }

      const displayClass = label === 'fake' ? 'Fake' : 'Real';
      const dispConf = (confidence * 100).toFixed(2);
      const fileType = data.file_type.charAt(0).toUpperCase() + data.file_type.slice(1);

      resultDiv.innerHTML = `
        <p><strong>File Type:</strong> ${fileType}</p>
        <p><strong>Prediction:</strong> ${displayClass}</p>
        <p><strong>Confidence:</strong> ${dispConf}%</p>
      `;

      if (label === 'fake') {
        resultDiv.style.color = '#c0392b';
        showSnowfall();
      } else {
        resultDiv.style.color = '#27ae60';
      }

    } catch (err) {
      console.error(err);
      resultDiv.innerHTML = `<p>🚫 Error: ${err.message}</p>`;
      resultDiv.style.color = "red";
    }
  });
});
