# FieldSense Edge AI Species ID
___
## Introduction
FieldSense will be a mobile app available on iPhone and Android that uses a local ML Image Classifier model to run inference offline. A local database will store information about the toxicity, edibility, safety, first aid and regulatory information about in-distribution species. The app will have models trained to be regional experts to reduce error and confusion.

## Data Pipeline
The data pipeline will be augmented with artificial intelligence and machine learning. A tiny triage model will be trained to recognize what photos are usable for training using a hand curated dataset. This triage model will also ship with the app to reject low-quality photos to minimize liability and user risk.

The triage model will be used to clean the production dataset to ensure high quality photos are used for training. Once a clean dataset is obtained, the regional production model will be trained on a high-fidelity dataset to achieve the best possible accuracy. The Regional production models will feature a dual head with one head trained to detect usability.

## Edge Inference
Given the high liability exposure of the application, appropriate precautions must be taken to ensure high quality photos are used to identify species. Below is an outline of how we might minimize risk and maximize accuracy.

### Viewfinder
We will use a viewfinder in the application to help guide the user to take high quality photos.
#### MVP:
For the MVP, the app will ask the user to select what they are trying to identify, plant, fungi, animal. Response will be stored as `mode` and the mode specific guidance will pop up instructing the user of how to target. From there the Viewfinder pops up and a target box is overlaid. The app will use low resource metrics based on frame samples. Metrics include stability from the onboard gyro, sharpness from Laplacian Variance and Sobel gradient energy, exposure from mean luminance and % of clipped blacks/whites, Centered subject based on saliency heat map with center weighted edge density. Once metrics meet standards user gets green light to capture.

#### Refined Product
For the end product we need a viewfinder that can also auto-capture and has more graphic guidance. The viewfinder may sample the camera feed and run the image through mobileSAM to confirm quality.

### Quick Triage/Crop
In the MVP the image will then be passed through a saliency heat map check to identify the top points for the MobileSAM mask. The mobileSAM masks and we run checks on that to confirm quality Based on area ratio -> `mask_px_cnt/img_px_cnt`, subject is not cutoff -> (% of px within 5-10px of edge), count of connected components (too many large components means multiple subjects/clutter), focus (blur within mask via laplacian). If the image fails these checks, the user is prompted to retake.

### Inference
The cropped image get fed into the model. We get a usable/unusable prediction and a species prediction. If the photo is unusable, we refuse to ID and prompt the user to retake. If the photo is usable we ID the species.

## Species Data
Once inference is run and we have a positive ID, we pull species data from the database. If the species is edible but has known toxic lookalikes, we pop up an assumption of risk checkbox that's recorded and queued to send the recording to the server. We may then offer the user information for how to distinguish the species from it's lookalikes with side-by-side photos. We only mark fungi as edible if they have no dangerous lookalikes in that region.
 - Plant Data: toxicity, precautions, first aid, risk level, edibility, medicinal properties, other uses, phenology, latin name, common name, distinguishing features, lookalikes
 - Fungi: Toxicity, precautions, first aid, risk level, edibility(very conservative), medicinal properties(conservative), other uses, phenology, latin name, common name, distinguishing features, lookalikes.
 - Terrestrial Animals: Latin Name, Common Name, danger level, behavior notes, deterrents, venom info, first aid, human conflict mitigation, distinguishing features, tracks and signs, lookalikes, habitat, conservation status
 - Aquatic animals: latin name, common name, fishing regs, harvest limits, legal gear, conservation status, Distinguishing features, size, habitat, depth range, Seasonal movements, activity pattern, aggression level, bite/spike/venom risk, edibility, slot, lookalikes.

## Browse feature
There must be a feature for the users to browse species by a few categories such as edibility, phenology, medicinal properties, etc.

## Logging
The app must include a feature to map and log species identification history so the users can revisit their honey-holes. We will create a local database where we store all positive ids from the user along with the gps coordinates.

## Regulatory updates
We must create an automated system for updating regulations and pushing the updates to the users device daily.
