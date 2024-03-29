## Clone the repository
git clone https://github.com/JaroslawBozek/ml-eng-test
## Build a docker image
docker build -t ml-eng-test .
## Build and run a container
docker run -d -p 3000:3000 ml-eng-test

##Send a cURL with an image in .png, .jpg or .pdf
```
curl -X POST -F "image=@extracted_page_xyz.png" "http://localhost:3000/run-inference?type=wall"
curl -X POST -F "image=@extracted_page_xyz.png" "http://localhost:3000/run-inference?type=tables"
```
