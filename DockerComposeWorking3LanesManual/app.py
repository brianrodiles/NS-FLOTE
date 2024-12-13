print("Starting script...")
import os
print("Importing os module completed.")
import logging
print("Importing logging module completed.")
import pandas as pd
print("Importing pandas module completed.")
import numpy as np
print("Importing numpy module completed.")
import tensorflow
print("Importing tensorflow.")
from sklearn.preprocessing import MinMaxScaler
print("Importing MinMaxScaler from sklearn.preprocessing completed.")
from sklearn.decomposition import PCA
print("Importing PCA from sklearn.decomposition completed.")
from tensorflow.keras.models import Sequential
print("Importing Sequential from tensorflow.keras.models completed.")
from tensorflow.keras.layers import Dense
print("Importing Dense from tensorflow.keras.layers completed.")
from tensorflow.keras.losses import MeanSquaredError
print("Importing MeanSquaredError from tensorflow.keras.losses completed.")
from tensorflow.keras import regularizers
print("Importing regularizers from tensorflow.keras completed.")
from tensorflow.keras.optimizers import Adam
print("Importing Adam from tensorflow.keras.optimizers completed.")
import flwr as fl
print("Importing flwr completed.")
from flwr.client import NumPyClient
print("Importing NumPyClient from flwr.client completed.")
from flwr.common import ndarrays_to_parameters, parameters_to_ndarrays, Metrics
print("Importing ndarrays_to_parameters, parameters_to_ndarrays, Metrics from flwr.common completed.")
from typing import List, Tuple
print("Importing List, Tuple from typing completed.")
print("All imports completed!")

# Set up logging
log_dir = os.getenv("LOG_PATH", "./logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "output.log"),
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)
logging.info("Starting anomaly detection system.")

# Load dataset (replace with actual dataset path)
dataset_path = "merged_Dataset_BearingTest_2.csv"
logging.info(f"Loading dataset from {dataset_path}")
data = pd.read_csv(dataset_path, index_col=0)

# Scale data to [0,1]
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(data)
logging.info("Data scaled successfully.")

# Reduce dimensionality with PCA
pca = PCA(n_components=2)
data_pca = pca.fit_transform(scaled_data)
logging.info("Dimensionality reduction with PCA completed.")

# Partition the data
NUM_PARTITIONS = 100
partitions = np.array_split(data_pca, NUM_PARTITIONS)
logging.info(f"Data partitioned into {NUM_PARTITIONS} parts.")

# Model creation function
def create_anomaly_detection_model(input_shape):
    logging.info(f"Creating anomaly detection model with input shape {input_shape}.")
    model = Sequential([
        Dense(10, activation='elu', kernel_initializer='glorot_uniform',
              kernel_regularizer=regularizers.l2(0.0), input_shape=(input_shape,)),
        Dense(2, activation='elu', kernel_initializer='glorot_uniform'),
        Dense(10, activation='elu', kernel_initializer='glorot_uniform'),
        Dense(input_shape, kernel_initializer='glorot_uniform')
    ])
    model.compile(optimizer=Adam(), loss='mse')
    return model

# Helper functions
def set_params(model, parameters):
    model.set_weights(parameters)

def get_params(model):
    return model.get_weights()

def calculate_accuracy(model, data, threshold=0.05):
    reconstructed = model.predict(data)
    mse = np.mean(np.power(data - reconstructed, 2), axis=1)
    predictions = (mse < threshold).astype(int)
    true_labels = np.ones(len(data))  # Assuming all test data is normal
    accuracy = np.mean(predictions == true_labels)
    logging.info(f"Accuracy calculated: {accuracy:.2f}")
    return accuracy

# Flower client
class AnomalyDetectionClient(NumPyClient):
    def __init__(self, train_data, test_data, round_num=1):
        self.model = create_anomaly_detection_model(input_shape=train_data.shape[1])
        self.train_data = train_data
        self.test_data = test_data
        self.round_num = round_num

    def fit(self, parameters, config):
        set_params(self.model, parameters)
        self.model.fit(self.train_data, self.train_data, epochs=1, batch_size=10, verbose=0)
        return get_params(self.model), len(self.train_data), {}

    def evaluate(self, parameters, config):
        set_params(self.model, parameters)
        loss = self.model.evaluate(self.test_data, self.test_data, verbose=0)
        threshold = max(0.05 - 0.005 * (self.round_num - 1), 0.02)
        accuracy = calculate_accuracy(self.model, self.test_data, threshold=threshold)
        self.round_num += 1
        return loss, len(self.test_data), {"accuracy": accuracy}

# Client function
def client_fn(context):
    partition_id = int(context.node_config["partition-id"])
    train_data, test_data = np.split(partitions[partition_id], [int(0.9 * len(partitions[partition_id]))])
    return AnomalyDetectionClient(train_data, test_data).to_client()

# Metric aggregation
def weighted_average(metrics: List[Tuple[int, Metrics]]) -> Metrics:
    accuracies = [num_examples * m["accuracy"] for num_examples, m in metrics]
    examples = [num_examples for num_examples, _ in metrics]
    return {"accuracy": sum(accuracies) / sum(examples)}

# Server function
def server_fn(context):
    model = create_anomaly_detection_model(input_shape=data_pca.shape[1])
    initial_parameters = ndarrays_to_parameters(get_params(model))

    strategy = fl.server.strategy.FedAvg(
        fraction_fit=0.1,
        fraction_evaluate=0.5,
        evaluate_metrics_aggregation_fn=weighted_average,
        initial_parameters=initial_parameters,
    )
    config = fl.server.ServerConfig(num_rounds=3)
    return fl.server.ServerAppComponents(strategy=strategy, config=config)

# Flower simulation
from flwr.client import ClientApp
from flwr.server import ServerApp
client_app = ClientApp(client_fn=client_fn)
server_app = ServerApp(server_fn=server_fn)

# Run the simulation
logging.info("Starting Flower simulation.")
from flwr.simulation import run_simulation
run_simulation(
    server_app=server_app, client_app=client_app, num_supernodes=NUM_PARTITIONS
)
logging.info("Flower simulation completed.")