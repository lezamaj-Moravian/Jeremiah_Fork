# Flask server endpoint details:

### `GET /`

* **Description:** Serves the main `index.html` frontend application.
* **Method:** `GET`
* **Response:**
    * `Content-Type: text/html`
    * The HTML, CSS, and JavaScript for the dashboard.

### `GET /data`

* **Description:** Fetches a complete list of all athletes, with their daily mileage logs nested inside each athlete object.
* **Method:** `GET`
* **Success Response (200 OK):**
    * `Content-Type: application/json`
    * **Body:** A JSON array of athlete objects.

    **Example JSON Response:**
    ```json
    [
      {
        "athlete_id": 1,
        "first_name": "John",
        "last_name": "Smith",
        "gender": "M",
        "mileage_goal": 30.0,
        "long_run_goal": 8.0,
        "mileage": [
          {
            "activity_id": 2,
            "date": "2025-11-13",
            "distance": 7.81,
            "activity_title": "None",
            "athlete_id": 1
          },
          {
            "activity_id": 1,
            "date": "2025-11-12",
            "distance": 4.12,
            "activity_title": "None",
            "athlete_id": 1
          }
        ]
      }
    ]
    ```

