# ------------------------------------------------------------------
#     _____ _     _ _
#    |  ___(_) __| | | ___
#    | |_  | |/ _` | |/ _ \
#    |  _| | | (_| | |  __/
#    |_|   |_|\__,_|_|\___|                              VAE Example
# ------------------------------------------------------------------
# Formation Introduction au Deep Learning  (FIDLE)
# CNRS/SARI/DEVLOG 2020 - S. Arias, E. Maldonado, JL. Parouty
# ------------------------------------------------------------------
# by JL Parouty (dec 2020), based on François Chollet example
#
# See : https://keras.io/examples/generative/vae

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# Note : https://www.tensorflow.org/guide/keras/save_and_serialize#custom_objects

class Sampling(keras.layers.Layer):
    '''A custom layer that receive (z_mean, z_var) and sample a z vector'''

    def call(self, inputs):
        z_mean, z_log_var = inputs
        batch = tf.shape(z_mean)[0]
        dim   = tf.shape(z_mean)[1]
        epsilon = tf.keras.backend.random_normal(shape=(batch, dim))
        return z_mean + tf.exp(0.5 * z_log_var) * epsilon
    

class VAE(keras.Model):
    '''A VAE model, built from given encoder, decoder'''
    
    def __init__(self, encoder=None, decoder=None, r_loss_factor=0.3, image_size=(28,28), **kwargs):
        super(VAE, self).__init__(**kwargs)
        self.encoder = encoder
        self.decoder = decoder
        self.r_loss_factor = r_loss_factor
        self.nb_pixels     = np.prod(image_size)
        print(f'Init VAE, with r_loss_factor={self.r_loss_factor} and image_size={image_size}')

        
    def call(self, inputs):
        z_mean, z_log_var, z = self.encoder(inputs)
        y_pred = self.decoder(z)
        return y_pred
                
        
    def train_step(self, data):
        
        if isinstance(data, tuple):
            data = data[0]
            
        with tf.GradientTape() as tape:
            z_mean, z_log_var, z = self.encoder(data)
            reconstruction       = self.decoder(z)
            reconstruction_loss  = tf.reduce_mean( keras.losses.binary_crossentropy(data, reconstruction) )
            reconstruction_loss *= self.nb_pixels
            kl_loss = 1 + z_log_var - tf.square(z_mean) - tf.exp(z_log_var)
            kl_loss = tf.reduce_mean(kl_loss)
            kl_loss *= -0.5
            total_loss = self.r_loss_factor*reconstruction_loss + (1-self.r_loss_factor)*kl_loss
            
        grads = tape.gradient(total_loss, self.trainable_weights)
        self.optimizer.apply_gradients(zip(grads, self.trainable_weights))
        
        return {
            "loss":                total_loss,
            "reconstruction_loss": reconstruction_loss,
            "kl_loss":             kl_loss,
        }
    
    
    def reload(self,filename):
        self.encoder = keras.models.load_model(f'{filename}-enc.h5', custom_objects={'Sampling': Sampling})
        self.decoder = keras.models.load_model(f'{filename}-dec.h5')
        print('Reloaded.')
        
    def save(self,filename):
        self.encoder.save(f'{filename}-enc.h5')
        self.decoder.save(f'{filename}-dec.h5')